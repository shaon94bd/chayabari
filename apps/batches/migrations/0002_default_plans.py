from django.db import migrations

PLANS = [
    dict(code="semester", name="Semester", price_bdt=1500, duration_days=180, max_members=40, sort_order=1,
         description="6 months for your whole batch — exhibitions, sales, auctions and chat."),
    dict(code="year", name="Full year", price_bdt=2500, duration_days=365, max_members=40, sort_order=2,
         description="12 months for your whole batch. Best value."),
    dict(code="year-plus", name="Full year — large batch", price_bdt=4000, duration_days=365, max_members=80,
         sort_order=3, description="12 months, up to 80 members."),
]


def add_plans(apps, schema_editor):
    Plan = apps.get_model("batches", "Plan")
    for p in PLANS:
        Plan.objects.get_or_create(code=p["code"], defaults=p)


class Migration(migrations.Migration):
    dependencies = [("batches", "0001_initial")]
    operations = [migrations.RunPython(add_plans, migrations.RunPython.noop)]
