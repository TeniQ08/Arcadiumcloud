from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import Client, TestCase
from django.utils import timezone

from accounts.models import User
from game_sessions.models import GameSession
from payments.models import Payment
from pricing.models import PricingPlan
from stations.models import Station


class AnalyticsApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username="admin", password="pass", role=User.Role.ADMIN)
        self.attendant = User.objects.create_user(username="att", password="pass", role=User.Role.ATTENDANT)
        self.plan_hour = PricingPlan.objects.create(
            name="1 Hour",
            package_duration_minutes=60,
            package_price=Decimal("100.00"),
            is_active=True,
        )
        self.plan_half = PricingPlan.objects.create(
            name="30 Minutes",
            package_duration_minutes=30,
            package_price=Decimal("60.00"),
            is_active=True,
        )
        self.station_one = Station.objects.create(name="PS5-01", pricing_plan=self.plan_hour, status=Station.Status.AVAILABLE)
        self.station_two = Station.objects.create(name="PS5-02", pricing_plan=self.plan_half, status=Station.Status.AVAILABLE)
        now = timezone.now()
        self.session_one = GameSession.objects.create(
            station=self.station_one,
            pricing_plan=self.plan_hour,
            plan_name_snapshot=self.plan_hour.name,
            duration_minutes_snapshot=60,
            price_snapshot=Decimal("100.00"),
            status=GameSession.Status.COMPLETED,
            start_time=now - timedelta(hours=2),
            expected_end_time=now - timedelta(hours=1),
            actual_end_time=now - timedelta(hours=1),
        )
        self.session_two = GameSession.objects.create(
            station=self.station_two,
            pricing_plan=self.plan_half,
            plan_name_snapshot=self.plan_half.name,
            duration_minutes_snapshot=30,
            price_snapshot=Decimal("60.00"),
            status=GameSession.Status.COMPLETED,
            start_time=now - timedelta(hours=1),
            expected_end_time=now - timedelta(minutes=30),
            actual_end_time=now - timedelta(minutes=30),
        )
        Payment.objects.create(
            session=self.session_one,
            amount_due=Decimal("100.00"),
            amount_paid=Decimal("100.00"),
            status=Payment.Status.PAID,
            method=Payment.Method.MPESA,
            paid_at=now - timedelta(hours=2),
        )
        Payment.objects.create(
            session=self.session_two,
            amount_due=Decimal("60.00"),
            amount_paid=Decimal("60.00"),
            status=Payment.Status.PAID,
            method=Payment.Method.MPESA,
            paid_at=now - timedelta(hours=1),
        )
        Payment.objects.create(
            session=self.session_two,
            amount_due=Decimal("60.00"),
            amount_paid=Decimal("0.00"),
            status=Payment.Status.CANCELLED,
            method=Payment.Method.MPESA,
            paid_at=now - timedelta(minutes=30),
        )

    def test_analytics_requires_authenticated_staff(self):
        response = self.client.get("/api/analytics/revenue/summary/")
        self.assertEqual(response.status_code, 403)

    def test_staff_can_read_revenue_summary(self):
        self.client.force_login(self.attendant)
        response = self.client.get("/api/analytics/revenue/summary/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["today_revenue"], "160.00")
        self.assertEqual(response.json()["paid_sessions"], 2)

    def test_revenue_by_station_counts_only_successful_payments(self):
        self.client.force_login(self.admin)
        response = self.client.get("/api/analytics/revenue/by-station/")

        self.assertEqual(response.status_code, 200)
        rows = {row["station_name"]: row for row in response.json()}
        self.assertEqual(rows["PS5-01"]["total_revenue"], "100.00")
        self.assertEqual(rows["PS5-02"]["total_revenue"], "60.00")

    def test_revenue_by_package(self):
        self.client.force_login(self.admin)
        response = self.client.get("/api/analytics/revenue/by-package/")

        self.assertEqual(response.status_code, 200)
        rows = {row["package_name"]: row for row in response.json()}
        self.assertEqual(rows["1 Hour"]["paid_sessions"], 1)
        self.assertEqual(rows["30 Minutes"]["total_revenue"], "60.00")

    def test_station_performance_includes_used_minutes_and_utilization(self):
        self.client.force_login(self.admin)
        response = self.client.get("/api/analytics/stations/performance/")

        self.assertEqual(response.status_code, 200)
        rows = {row["station_name"]: row for row in response.json()}
        self.assertEqual(rows["PS5-01"]["total_sessions"], 1)
        self.assertEqual(rows["PS5-01"]["total_used_minutes"], 60)
        self.assertGreaterEqual(rows["PS5-01"]["utilization_percentage"], 0)

    def test_occupancy_daily_and_weekly(self):
        self.client.force_login(self.admin)
        daily = self.client.get("/api/analytics/occupancy/?view=daily")
        weekly = self.client.get("/api/analytics/occupancy/?view=weekly")

        self.assertEqual(daily.status_code, 200)
        self.assertEqual(weekly.status_code, 200)
        self.assertEqual(daily.json()["total_used_minutes"], 90)
        self.assertGreaterEqual(len(weekly.json()["buckets"]), 1)

    def test_peak_hours_returns_24_buckets(self):
        self.client.force_login(self.admin)
        response = self.client.get("/api/analytics/peak-hours/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 24)
        self.assertEqual(sum(row["sessions_count"] for row in data), 2)
