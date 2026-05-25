from django.contrib import admin
from django.contrib.gis import admin as gis_admin  # GISModelAdmin
from django import forms
from django.contrib.gis import forms as gis_forms
from django.contrib import messages
from .models import Road, RoadVertex, Village, Mandi, State, District, AttributeType, Product, ProductSubmission, SubmittedProduct

# ---------- Inline for Submitted Products ----------
class SubmittedProductInline(admin.TabularInline):
    model = SubmittedProduct
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('product', 'weight_kg', 'harvest_month', 'created_at')
    raw_id_fields = ('product',)
    
    def has_add_permission(self, request, obj=None):
        return True
    
    def has_delete_permission(self, request, obj=None):
        return True

# ---------- Village ----------
@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'latitude', 'longitude')
    search_fields = ('name', 'district__district_name')
    list_filter = ('district',)


# ---------- Mandi ----------
@admin.register(Mandi)
class MandiAdmin(admin.ModelAdmin):
    list_display = ('mandi_name', 'mandi_type', 'latitude', 'longitude', 'district')
    search_fields = ('mandi_name', 'mandi_type', 'district__district_name')
    list_filter = ('district', 'mandi_type')


# ---------- State ----------
@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("state_name", "country")
    search_fields = ("state_name", "country")


# ---------- District ----------
@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("id", "district_name", "get_state_name")
    search_fields = ("district_name", "state__state_name")
    list_filter = ("state",)

    def get_state_name(self, obj):
        return obj.state.state_name
    get_state_name.short_description = "State"


# ---------- Road ----------
@admin.register(Road)
class RoadAdmin(gis_admin.GISModelAdmin):
    list_display = (
        'id', 'name', 'highway', 'width', 'length',
        'type', 'lanes', 'calculated_cost'
    )
    list_filter = ('highway', 'lanes')
    search_fields = ('name', 'osm_id', 'fid')
    ordering = ('id',)

    # Default map position (Punjab approx.)
    default_lon = 74.5
    default_lat = 30.9
    default_zoom = 7

    def calculated_cost(self, obj):
        try:
            return obj.geom.length  # length in meters
        except Exception:
            return None
    calculated_cost.short_description = "Cost (meters)"


# ---------- RoadVertex ----------
class RoadVertexForm(forms.ModelForm):
    class Meta:
        model = RoadVertex
        fields = '__all__'
        widgets = {
            # 🔑 use the correct DB column name "the_geom"
            'the_geom': gis_forms.OSMWidget(attrs={
                'map_width': 800,
                'map_height': 500,
                'default_lon': 74.5,   # Punjab longitude
                'default_lat': 30.9,   # Punjab latitude
                'default_zoom': 7,
            })
        }


@admin.register(RoadVertex)
class RoadVertexAdmin(gis_admin.GISModelAdmin):
    form = RoadVertexForm
    list_display = ('id', 'cnt', 'chk', 'ein', 'eout')
    search_fields = ('id', 'cnt', 'chk', 'ein', 'eout')
    list_filter = ('cnt', 'chk')
    ordering = ('id',)


@admin.register(AttributeType)
class AttributeTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "created_at", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("created_at", "updated_at")
    ordering = ("name",)
    
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "product_name", "attribute_type", "created_at", "updated_at")
    search_fields = ("product_name", "attribute_type__name")
    list_filter = ("attribute_type", "created_at")
    ordering = ("product_name",)
    
    
@admin.register(ProductSubmission)
class ProductSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'village', 'district_name', 'state_name', 
        'submission_date', 'submitted_by', 
        'product_count', 'total_weight', 'created_at'
    )
    list_filter = (
        'submission_date', 
        'village__district__state', 
        'village__district', 
        'created_at',
    )
    search_fields = (
        'village__name', 
        'village__district__district_name',
        'village__district__state__state_name', 
        'submitted_by__username',
        'submitted_products__product__product_name'
    )
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('village', 'submitted_by')
    inlines = [SubmittedProductInline]  # Now this will work
    date_hierarchy = 'submission_date'
    list_per_page = 20
    list_select_related = ('village__district__state', 'submitted_by')
    
    fieldsets = (
        ('Submission Information', {
            'fields': (
                'village', 
                'submission_date', 
                'submitted_by'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def district_name(self, obj):
        return obj.village.district.district_name if obj.village.district else 'No District'
    district_name.short_description = 'District'
    district_name.admin_order_field = 'village__district__district_name'

    def state_name(self, obj):
        return obj.village.district.state.state_name if obj.village.district else 'No State'
    state_name.short_description = 'State'
    state_name.admin_order_field = 'village__district__state__state_name'

    def product_count(self, obj):
        return obj.submitted_products.count()
    product_count.short_description = 'Products Count'

    def total_weight(self, obj):
        from django.db.models import Sum
        total = obj.submitted_products.aggregate(
            total_weight=Sum('weight_kg')
        )['total_weight'] or 0
        return f"{total} kg"
    total_weight.short_description = 'Total Weight'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'village__district__state', 
            'submitted_by'
        ).prefetch_related('submitted_products', 'submitted_products__product')

    # Custom actions
    actions = ['calculate_total_weight_action']

    def calculate_total_weight_action(self, request, queryset):
        from django.db.models import Sum
        total_weight = 0
        submission_count = 0
        
        for submission in queryset:
            weight = submission.submitted_products.aggregate(
                total=Sum('weight_kg')
            )['total'] or 0
            total_weight += weight
            submission_count += 1
        
        self.message_user(
            request, 
            f'Total weight of {submission_count} submission(s): {total_weight} kg', 
            messages.INFO
        )
    calculate_total_weight_action.short_description = "Calculate total weight of selected submissions"


# ---------- SubmittedProduct Admin ----------
@admin.register(SubmittedProduct)
class SubmittedProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'product_name', 
        'attribute_type', 
        'submission_info', 
        'village_name',
        'district_name',
        'state_name',
        'weight_kg', 
        'harvest_month', 
        'submission_date',
        'created_at'
    )
    list_filter = (
        'harvest_month', 
        'product__attribute_type',
        'submission__submission_date', 
        'submission__village__district__state',
        'submission__village__district',
        'created_at'
    )
    search_fields = (
        'product__product_name', 
        'submission__village__name',
        'submission__village__district__district_name',
        'submission__village__district__state__state_name'
    )
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('submission', 'product')
    list_per_page = 30
    
    fieldsets = (
        ('Product Information', {
            'fields': (
                'submission', 
                'product',
                'weight_kg', 
                'harvest_month'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def product_name(self, obj):
        return obj.product.product_name
    product_name.short_description = 'Product Name'
    product_name.admin_order_field = 'product__product_name'

    def attribute_type(self, obj):
        return obj.product.attribute_type.name
    attribute_type.short_description = 'Product Type'
    attribute_type.admin_order_field = 'product__attribute_type__name'

    def submission_info(self, obj):
        return f"Submission #{obj.submission.id}"
    submission_info.short_description = 'Submission'
    submission_info.admin_order_field = 'submission__id'

    def village_name(self, obj):
        return obj.submission.village.name
    village_name.short_description = 'Village'
    village_name.admin_order_field = 'submission__village__name'

    def district_name(self, obj):
        return obj.submission.village.district.district_name if obj.submission.village.district else 'No District'
    district_name.short_description = 'District'
    district_name.admin_order_field = 'submission__village__district__district_name'

    def state_name(self, obj):
        return obj.submission.village.district.state.state_name if obj.submission.village.district else 'No State'
    state_name.short_description = 'State'
    state_name.admin_order_field = 'submission__village__district__state__state_name'

    def submission_date(self, obj):
        return obj.submission.submission_date
    submission_date.short_description = 'Submission Date'
    submission_date.admin_order_field = 'submission__submission_date'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'submission__village__district__state',
            'product__attribute_type'
        )

    # Custom actions for SubmittedProduct
    actions = ['calculate_total_weight_action']

    def calculate_total_weight_action(self, request, queryset):
        total_weight = sum(product.weight_kg for product in queryset)
        product_count = queryset.count()
        self.message_user(
            request, 
            f'Total weight of {product_count} product(s): {total_weight} kg', 
            messages.INFO
        )
    calculate_total_weight_action.short_description = "Calculate total weight of selected products"