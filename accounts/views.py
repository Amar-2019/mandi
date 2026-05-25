from shapely.ops import linemerge
from shapely import wkt
from shapely.geometry import LineString, mapping
from .models import RoadVertex, SubmittedProduct
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db import connection
from django.shortcuts import render
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Village, Mandi, District, State, AttributeType, ProductSubmission, Product
from django.views.decorators.csrf import csrf_exempt


def login_view(request):
    if request.method == "POST":
        userId = request.POST.get("userId")
        password = request.POST.get("password")
        user = authenticate(request, username=userId, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")  # URL name, not template
        else:
            messages.error(request, "Invalid ID or Password")

    return render(request, "login.html")


@login_required
def dashboard_view(request):
    villages = Village.objects.select_related(
        "district").all().order_by("name")
    mandis = Mandi.objects.select_related(
        "district").all().order_by("mandi_name")
    states = State.objects.all().order_by("state_name")
    districts = District.objects.select_related(
        "state").all().order_by("district_name")
    context = {
        "villages": villages,
        "mandis": mandis,
        "states": states,
        "districts": districts,
    }
    return render(request, "home.html", context)

# In your views.py


@csrf_exempt
def product_view(request):
    villages = Village.objects.all().select_related('district')
    attribute_types = AttributeType.objects.prefetch_related('products').all()

    additional_attributes = AttributeType.objects.all()

    products_dict = {}
    for attr in attribute_types:
        products_dict[attr.name] = list(
            attr.products.values("id", "product_name"))

    context = {
        'villages': villages,
        'attribute_types': attribute_types,
        'additional_attributes': additional_attributes,
        'products_dict': products_dict,
    }

    return render(request, "mehak.html", context)


@csrf_exempt
def submit_products(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            village_name = data.get('village')
            submission_date = data.get('date')
            products_data = data.get('products', [])

            # Get village instance
            try:
                village = Village.objects.get(name=village_name)
            except Village.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Village "{village_name}" not found'
                }, status=400)

            # Create product submission
            submission = ProductSubmission.objects.create(
                village=village,
                submission_date=submission_date,
                submitted_by=request.user if request.user.is_authenticated else None
            )

            # Create submitted products
            submitted_products = []
            for product_data in products_data:
                try:
                    product = Product.objects.get(id=product_data['id'])

                    # Extract numeric value from weight string (e.g., "10 kg" -> 10.00)
                    weight_str = product_data['weight_kg']
                    weight_value = float(weight_str.replace(' kg', '').strip())

                    submitted_product = SubmittedProduct(
                        submission=submission,
                        product=product,
                        weight_kg=weight_value,
                        harvest_month=product_data['harvest_month']
                    )
                    submitted_products.append(submitted_product)

                except Product.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Product with ID {product_data["id"]} not found'
                    }, status=400)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid weight format for product {product_data["product_name"]}'
                    }, status=400)

            # Bulk create submitted products
            SubmittedProduct.objects.bulk_create(submitted_products)

            return JsonResponse({
                'success': True,
                'message': f'Successfully submitted {len(submitted_products)} products',
                'submission_id': submission.id
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'success': False,
        'error': 'Only POST method allowed'
    }, status=405)


@login_required
def village_view(request):
    districts = District.objects.select_related('state').all()
    villages = Village.objects.select_related('district').all()

    if request.method == "POST":
        name = request.POST.get("villageName")
        district_id = request.POST.get("district")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        if name and district_id and latitude and longitude:
            try:
                district = District.objects.get(id=district_id)
                Village.objects.create(
                    name=name,
                    district=district,
                    latitude=latitude,
                    longitude=longitude
                )
                messages.success(request, "Village saved successfully!")
                return redirect("village")
            except District.DoesNotExist:
                messages.error(request, "Invalid district selected.")
        else:
            messages.error(request, "Please fill in all fields.")

    context = {
        'districts': districts,
        'villages': villages,
    }
    return render(request, "village_list.html", context)

# API view for getting submitted products by village


@login_required
def get_submitted_products(request):
    village_name = request.GET.get('village')

    if not village_name:
        return JsonResponse({'success': False, 'error': 'Village name required'})

    try:
        # Get village details
        village = Village.objects.select_related(
            'district__state').get(name=village_name)

        # Get all submissions for this village
        submissions = ProductSubmission.objects.filter(village=village).prefetch_related(
            'submitted_products__product__attribute_type'
        )

        products_data = []
        for submission in submissions:
            for submitted_product in submission.submitted_products.all():
                products_data.append({
                    'product_name': submitted_product.product.product_name,
                    'product_type': submitted_product.product.attribute_type.name,
                    'weight_kg': str(submitted_product.weight_kg),
                    'harvest_month': submitted_product.harvest_month,
                    'submission_date': submission.submission_date.strftime('%Y-%m-%d'),
                })

        return JsonResponse({
            'success': True,
            'village': {
                'name': village.name,
                'district': village.district.district_name if village.district else 'No District',
                'state': village.district.state.state_name if village.district and village.district.state else 'No State',
                'latitude': str(village.latitude),
                'longitude': str(village.longitude),
            },
            'products': products_data
        })

    except Village.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Village not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def mandi_view(request):
    if request.method == "POST":
        mandi_name = request.POST.get("mandiName")
        mandi_type = request.POST.get("mandiType")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        if mandi_name and mandi_type and latitude and longitude:
            Mandi.objects.create(
                mandi_name=mandi_name,
                mandi_type=mandi_type,
                latitude=latitude,
                longitude=longitude
            )
            messages.success(request, "Mandi saved successfully!")
            return redirect("dashboard")
        else:
            messages.error(request, "Please fill in all fields.")

    return render(request, "mandi_list.html")


@login_required
def villages_list_view(request):
    # Fetch all villages and products
    villages = Village.objects.select_related(
        'district__state').all().order_by('name')

    context = {
        "villages": villages,          # Changed variable name to match template
    }

    return render(request, 'villages_list.html', context)


@login_required
def mandi_list_view(request):
    # Fetch all mandis with related district and state
    mandis = Mandi.objects.select_related(
        'district__state').all().order_by('mandi_name')

    # Send to template
    context = {
        "mandis": mandis  # matches template loop
    }
    return render(request, "mandi_list.html", context)


# views.py

# --- Road type lists ---
HIGHWAY_TYPES = [
    'motorway', 'trunk', 'trunk_link', 'primary', 'primary_link', 'expressway'
]
LOCAL_TYPES = [
    'secondary', 'secondary_link', 'tertiary', 'tertiary_link', 'residential',
    'living_street', 'service', 'unclassified', 'pedestrian', 'track', 'road', 'construction'
]


@login_required
def route(request):
    try:
        src_lat = float(request.GET.get('src_lat'))
        src_lng = float(request.GET.get('src_lng'))
        dst_lat = float(request.GET.get('dst_lat'))
        dst_lng = float(request.GET.get('dst_lng'))
        route_type = request.GET.get('type', 'shortest').lower()
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid coordinates"}, status=400)

    if route_type not in ["shortest", "highway", "local"]:
        return JsonResponse({"error": "Invalid route type"}, status=400)

    with connection.cursor() as cursor:
        # Snap source
        cursor.execute("""
            SELECT id
            FROM five_state_roads_vertices_pgr
            ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s,%s),4326)
            LIMIT 1
        """, [src_lng, src_lat])
        src_node = cursor.fetchone()

        # Snap destination
        cursor.execute("""
            SELECT id
            FROM five_state_roads_vertices_pgr
            ORDER BY the_geom <-> ST_SetSRID(ST_Point(%s,%s),4326)
            LIMIT 1
        """, [dst_lng, dst_lat])
        dst_node = cursor.fetchone()

        if not src_node or not dst_node:
            return JsonResponse({"error": "No nearby nodes found"}, status=404)

        src_node_id, dst_node_id = src_node[0], dst_node[0]

        # Cost expression based on route type
        if route_type == "shortest":
            cost_expr = "length"
        elif route_type == "highway":
            cost_expr = (
                f"cost * CASE WHEN highway IN ({','.join([f'\'{t}\'' for t in HIGHWAY_TYPES])
                                                }) THEN 1 ELSE 10 END"
            )
        else:  # local
            cost_expr = (
                f"cost * CASE WHEN highway IN ({','.join([f'\'{t}\'' for t in LOCAL_TYPES])
                                                }) THEN 1 ELSE 4 END"
            )

        # Run Dijkstra, include width in the main query
        edge_sql = f"""
            SELECT id, source, target, width, {cost_expr} AS cost, {cost_expr} AS reverse_cost
            FROM five_state_roads
        """
        cursor.execute(f"""
            SELECT d.seq, d.node, d.edge, d.cost, r.width, ST_AsGeoJSON(r.geom) AS geom
            FROM pgr_dijkstra(
                $$ {edge_sql} $$,
                %s, %s,
                directed := false
            ) AS d
            JOIN five_state_roads r ON d.edge = r.id
        """, [src_node_id, dst_node_id])
        rows = cursor.fetchall()

        if not rows:
            return JsonResponse({
                "error": f"No {route_type} route found",
                "features": [],
                "distance_km": None
            })

        # Build GeoJSON features
        features = []
        total_distance = 0
        for seq, node, edge, cost, width, geom_json in rows:
            if geom_json:
                # Determine color based on width
                if width is None:
                    color = "gray"
                elif width < 4:
                    color = "red"
                elif 4 <= width < 6:
                    color = "orange"
                elif 6 <= width <= 10:
                    color = "blue"
                else:
                    color = "black"

                features.append({
                    "type": "Feature",
                    "geometry": json.loads(geom_json),
                    "properties": {
                        "seq": seq,
                        "cost_m": cost,
                        "node": node,
                        "edge": edge,
                        "width": width,
                        "color": color
                    }
                })
                total_distance += cost

        # # --- Get the entire route geometry as a single LineString ---
        # cursor.execute(f"""
        #     SELECT ST_AsGeoJSON(ST_Union(r.geom))
        #     FROM pgr_dijkstra(
        #         $$ {edge_sql} $$,
        #         %s, %s, directed := false
        #     ) AS d
        #     JOIN five_state_roads r ON d.edge = r.id
        # """, [src_node_id, dst_node_id])
        # route_union_geojson = cursor.fetchone()[0]

        # # --- Find toll plazas within ~100 meters of the route ---
        # cursor.execute("""
        #     SELECT id, name, ST_AsGeoJSON(geom) AS geom
        #     FROM tool_plaza
        #     WHERE ST_DWithin(
        #         geom::geography,
        #         ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)::geography,
        #         100  -- 100 meters
        #     )
        # """, [route_union_geojson])
        # tolls = cursor.fetchall()

        # # --- Add toll plazas as GeoJSON features ---
        # for toll_id, toll_name, toll_geom in tolls:
        #     features.append({
        #         "type": "Feature",
        #         "geometry": json.loads(toll_geom),
        #         "properties": {
        #             "id": toll_id,
        #             "name": toll_name,
        #             "icon": "toll"  # frontend will recognize this
        #         }
        #     })

        return JsonResponse({
            "type": "FeatureCollection",
            "features": features,
            "distance_km": round(total_distance / 1000, 2)
        })
