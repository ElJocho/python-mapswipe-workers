from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import Area
from django.db import models
from django.db.models.functions import Cast
from django_cte import CTEManager


def calculate_geo_area(field):
    """
    ST_Area((field)::geography(GEOMETRY,4326))
        - same to (ST_Area(geom::geography))
    Response: area_sqkm
    """
    return Area(
        Cast(
            field,
            GeometryField(geography=True),  # to_sql: field::geography
        )
        / 1000000
    )


class Model(models.Model):
    cte_objects = CTEManager()
    objects = models.Manager()

    class Meta:
        abstract = True
