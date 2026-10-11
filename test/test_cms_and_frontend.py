from django.test import Client, TestCase

from authentication.models import User
from settings.models import ContactMessage, Page, Publication, ResearchTool, Setting, TeamMember


class CMSAndFrontendTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Regular user
        self.regular_user = User.objects.create_user(
            username="regular_user",
            firstName="Regular",
            lastName="User",
        )
        self.regular_user.set_password("Pass123!")
        self.regular_user.save()

        # Staff user (not superuser)
        self.staff_user = User.objects.create_user(
            username="staff_user",
            firstName="Staff",
            lastName="Member",
        )
        self.staff_user.is_staff = True
        self.staff_user.is_superuser = False
        self.staff_user.set_password("Pass123!")
        self.staff_user.save()

        # Superadmin user
        self.superadmin = User.objects.create_user(
            username="superadmin_user",
            firstName="Super",
            lastName="Admin",
        )
        self.superadmin.is_staff = True
        self.superadmin.is_superuser = True
        self.superadmin.set_password("Pass123!")
        self.superadmin.save()

    # -------------------------------------------------------------------------
    # 1. Access Control Tests
    # -------------------------------------------------------------------------
    def test_anonymous_user_blocked_from_cms(self):
        response = self.client.get("/dashboard/cms/")
        self.assertIn(response.status_code, [302, 401, 403])

    def test_regular_user_blocked_from_cms(self):
        self.client.force_login(self.regular_user)
        response = self.client.get("/dashboard/cms/")
        self.assertIn(response.status_code, [302, 403])

    def test_staff_non_superuser_blocked_from_cms(self):
        self.client.force_login(self.staff_user)
        response = self.client.get("/dashboard/cms/")
        # Superadmins only! Staff without superuser must be blocked
        self.assertIn(response.status_code, [302, 403])

    def test_superadmin_can_access_all_cms_views(self):
        self.client.force_login(self.superadmin)
        endpoints = [
            "/dashboard/cms/",
            "/dashboard/cms/pages",
            "/dashboard/cms/team",
            "/dashboard/cms/publications",
            "/dashboard/cms/tools",
            "/dashboard/cms/messages",
            "/dashboard/cms/settings",
        ]
        for ep in endpoints:
            response = self.client.get(ep)
            self.assertEqual(response.status_code, 200, f"Endpoint {ep} failed with status {response.status_code}")

    # -------------------------------------------------------------------------
    # 2. CMS CRUD Operations
    # -------------------------------------------------------------------------
    def test_cms_save_and_delete_page(self):
        self.client.force_login(self.superadmin)
        # Create
        response = self.client.post(
            "/dashboard/cms/pages/save",
            {
                "title": "Ethics & IRB Approval",
                "slug": "ethics-irb",
                "content": "<p>Approved under protocol 2026-CKDU-01.</p>",
                "nav": "on",
                "footer": "on",
            },
        )
        self.assertIn(response.status_code, [200, 302])
        page = Page.objects.get(slug="ethics-irb")
        self.assertEqual(page.title, "Ethics & IRB Approval")
        self.assertTrue(page.nav)

        # Delete
        del_resp = self.client.post("/dashboard/cms/pages/delete", {"id": page.id})
        self.assertEqual(del_resp.status_code, 200)
        self.assertFalse(Page.objects.filter(slug="ethics-irb").exists())

    def test_cms_save_and_delete_team_member(self):
        self.client.force_login(self.superadmin)
        response = self.client.post(
            "/dashboard/cms/team/save",
            {
                "name": "Dr. Test Scientist",
                "role": "Lead Geneticist",
                "affiliation": "Genomics Institute",
                "bio": "Investigating rare gene variants.",
                "avatar": "img/avatar.jpg",
                "email": "scientist@biom.lk",
                "order": 99,
                "is_active": "on",
            },
        )
        self.assertIn(response.status_code, [200, 302])
        member = TeamMember.objects.get(name="Dr. Test Scientist")
        self.assertEqual(member.role, "Lead Geneticist")

        # Delete
        del_resp = self.client.post("/dashboard/cms/team/delete", {"id": member.id})
        self.assertEqual(del_resp.status_code, 200)
        self.assertFalse(TeamMember.objects.filter(id=member.id).exists())

    def test_cms_save_and_delete_publication(self):
        self.client.force_login(self.superadmin)
        response = self.client.post(
            "/dashboard/cms/publications/save",
            {
                "title": "New Biomarker Paper 2026",
                "authors": "Test, A., et al.",
                "journal": "Journal of Nephrology",
                "year": 2026,
                "doi": "10.1000/182",
                "citation_count": 5,
                "is_featured": "on",
                "is_active": "on",
            },
        )
        self.assertIn(response.status_code, [200, 302])
        pub = Publication.objects.get(title="New Biomarker Paper 2026")
        self.assertTrue(pub.is_featured)

        # Delete
        del_resp = self.client.post("/dashboard/cms/publications/delete", {"id": pub.id})
        self.assertEqual(del_resp.status_code, 200)
        self.assertFalse(Publication.objects.filter(id=pub.id).exists())

    def test_cms_save_and_delete_tool(self):
        self.client.force_login(self.superadmin)
        response = self.client.post(
            "/dashboard/cms/tools/save",
            {
                "name": "Cohort Visualizer",
                "category": "Data Exploration",
                "summary": "Interactive 3D UMAP projection",
                "url": "/tools/umap",
                "badge": "Beta",
                "order": 10,
                "is_active": "on",
            },
        )
        self.assertIn(response.status_code, [200, 302])
        tool = ResearchTool.objects.get(name="Cohort Visualizer")
        self.assertEqual(tool.badge, "Beta")

        # Delete
        del_resp = self.client.post("/dashboard/cms/tools/delete", {"id": tool.id})
        self.assertEqual(del_resp.status_code, 200)
        self.assertFalse(ResearchTool.objects.filter(id=tool.id).exists())

    def test_cms_messages_toggle_and_delete(self):
        self.client.force_login(self.superadmin)
        msg = ContactMessage.objects.create(
            name="Inquirer",
            email="inq@test.com",
            subject="Question",
            message="Hello BIOM team",
            is_read=False,
        )
        toggle_resp = self.client.post("/dashboard/cms/messages/toggle", {"id": msg.id})
        self.assertEqual(toggle_resp.status_code, 200)
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

        del_resp = self.client.post("/dashboard/cms/messages/delete", {"id": msg.id})
        self.assertEqual(del_resp.status_code, 200)
        self.assertFalse(ContactMessage.objects.filter(id=msg.id).exists())

    def test_cms_save_settings(self):
        self.client.force_login(self.superadmin)
        response = self.client.post(
            "/dashboard/cms/settings/save",
            {
                "site_title": "BIOM Platform Updated",
                "hero_subtitle": "New subtitle for CKDu research.",
                "contact_email": "contact@biom.lk",
            },
        )
        self.assertIn(response.status_code, [200, 302])
        setting = Setting.objects.get(key="site_title", tag="cms")
        self.assertEqual(setting.value, "BIOM Platform Updated")

    # -------------------------------------------------------------------------
    # 3. Frontend Pages & Form Submissions
    # -------------------------------------------------------------------------
    def test_frontend_home_page_renders_with_cms_content(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BIOM: Biomedical Omics Knowledgebase")
        self.assertContains(response, "Chronic Kidney Disease of Unknown Etiology")

    def test_frontend_about_page_renders(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About the Initiative")

    def test_frontend_team_page_renders(self):
        response = self.client.get("/team/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Our Research Team")

    def test_frontend_publications_page_renders(self):
        response = self.client.get("/publications/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Publications & Research")

    def test_frontend_tools_page_renders(self):
        response = self.client.get("/tools/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Research Tools & Utilities")

    def test_frontend_contact_page_and_submission(self):
        # GET
        response = self.client.get("/contact/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contact Our Research Team")

        # POST submission on /contact/
        post_resp = self.client.post(
            "/contact/",
            {
                "name": "Dr. Field Researcher",
                "email": "field.res@institution.org",
                "subject": "Access to Urine Proteomics Data",
                "message": "We would like to compare with our Latin American cohorts.",
            },
        )
        self.assertIn(post_resp.status_code, [200, 302])
        self.assertTrue(ContactMessage.objects.filter(email="field.res@institution.org").exists())

    def test_frontend_home_contact_submit(self):
        post_resp = self.client.post(
            "/contact-submit",
            {
                "name": "Home Page Inquirer",
                "email": "home.inq@biom.org",
                "subject": "Collaborative Inquiry",
                "message": "Requesting discussion on cohort accession.",
            },
        )
        self.assertIn(post_resp.status_code, [200, 302])
        self.assertTrue(ContactMessage.objects.filter(email="home.inq@biom.org").exists())

    def test_frontend_dynamic_page_route(self):
        Page.objects.create(
            slug="open-data-policy",
            title="Open Data Policy",
            content="<p>All data is licensed under CC-BY 4.0.</p>",
        )
        response = self.client.get("/page/open-data-policy")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Open Data Policy")
        self.assertContains(response, "CC-BY 4.0")
