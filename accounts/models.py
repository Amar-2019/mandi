from django.db import models
from django.contrib.gis.db import models as geomodels
from django.contrib.auth.models import User  # Add this import


class State(models.Model):
    state_name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, default="India")

    def __str__(self):
        return self.state_name


class District(models.Model):
    state = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        related_name="districts",
        default=1  # adjust based on your data
    )
    district_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.district_name}, {self.state.state_name}"


class Village(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name="villages",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name}, {self.district.district_name if self.district else 'No District'}"


class Mandi(models.Model):
    MANDI_TYPE_CHOICES = [
        ("grain", "Grain"),
        ("vegetable", "Vegetable"),
        ("fruit", "Fruit"),
        ("other", "Other"),
    ]

    mandi_name = models.CharField(max_length=100)
    mandi_type = models.CharField(
        max_length=50,
        choices=MANDI_TYPE_CHOICES,
        default="other"
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name="mandis",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.mandi_name}, {self.district.district_name if self.district else 'No District'}"


class Road(geomodels.Model):  # ✅ GeoDjango model
    id = models.BigIntegerField(primary_key=True)
    geom = geomodels.LineStringField(srid=4326)  # ✅ enforce LineString
    fid = models.IntegerField(null=True, blank=True)
    osm_id = models.BigIntegerField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    highway = models.CharField(max_length=100, null=True, blank=True)
    lanes = models.IntegerField(default=1)
    width = models.FloatField(null=True, blank=True)
    length = models.FloatField(null=True, blank=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    source = models.IntegerField(null=True, blank=True)
    target = models.IntegerField(null=True, blank=True)
    cost = models.FloatField(null=True, blank=True)           # forward cost
    reverse_cost = models.FloatField(null=True, blank=True)   # reverse cost

    class Meta:
        db_table = 'roads_punjab'
        managed = False

    def __str__(self):
        return self.name or f"Road {self.id}"


class RoadVertex(geomodels.Model):   # 👈 use geomodels.Model
    id = models.BigIntegerField(primary_key=True)
    cnt = models.IntegerField(null=True, blank=True)
    chk = models.IntegerField(null=True, blank=True)
    ein = models.IntegerField(null=True, blank=True)
    eout = models.IntegerField(null=True, blank=True)

    # ✅ PointField must come from geomodels
    the_geom = geomodels.PointField(srid=4326, db_column="the_geom")

    class Meta:
        managed = False
        db_table = "roads_punjab_vertices_pgr"

    def __str__(self):
        return f"Vertex {self.id}"


class AttributeType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(
        auto_now_add=True)  # timestamp when created
    updated_at = models.DateTimeField(
        auto_now=True)      # timestamp when updated

    class Meta:
        db_table = "attribute_type"
        verbose_name = "Attribute Type"
        verbose_name_plural = "Attribute Types"

    def __str__(self):
        return self.name


class Product(models.Model):
    product_name = models.CharField(max_length=150)
    attribute_type = models.ForeignKey(
        AttributeType,
        on_delete=models.CASCADE,
        related_name="products"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product"
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.product_name


class ProductSubmission(models.Model):
    village = models.ForeignKey(
        Village,
        on_delete=models.CASCADE,
        related_name="product_submissions"
    )
    submission_date = models.DateField()
    submitted_by = models.ForeignKey(
        User,  # ✅ Added the missing User model reference
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_submission"
        verbose_name = "Product Submission"
        verbose_name_plural = "Product Submissions"

    def __str__(self):
        return f"{self.village.name} - {self.submission_date}"


class SubmittedProduct(models.Model):
    MONTH_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]

    submission = models.ForeignKey(
        ProductSubmission,
        on_delete=models.CASCADE,
        related_name="submitted_products"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="submissions"
    )
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2)
    harvest_month = models.CharField(
        max_length=20,
        choices=MONTH_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "submitted_product"
        verbose_name = "Submitted Product"
        verbose_name_plural = "Submitted Products"

    def __str__(self):
        return f"{self.product.product_name} - {self.weight_kg}kg - {self.harvest_month}"
