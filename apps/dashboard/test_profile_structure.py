from html.parser import HTMLParser

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.profiles.models import CandidateProfile, ProfileSkill


class _Node:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.parent = parent
        self.children = []
        self.text = ""

    def descendants(self, tag=None):
        for child in self.children:
            if tag is None or child.tag == tag:
                yield child
            yield from child.descendants(tag)

    def has_class(self, class_name):
        return class_name in self.attrs.get("class", "").split()

    def is_descendant_of(self, ancestor):
        node = self.parent
        while node is not None:
            if node is ancestor:
                return True
            node = node.parent
        return False


class _StructureParser(HTMLParser):
    VOID_ELEMENTS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("document")
        self.stack = [self.root]
        self.mismatches = []

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in self.VOID_ELEMENTS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            current = self.stack[-1].tag if len(self.stack) > 1 else "document"
            self.mismatches.append((tag, current))
            return
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].text += data


class DashboardProfileStructureTests(TestCase):
    def setUp(self):
        self.user = User(username="profile-structure", email="structure@example.test")
        self.user.set_password("password123")
        self.user.save()
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            target_country="France",
        )
        ProfileSkill.objects.create(
            profile=self.profile,
            raw_name="Python",
            normalized_name="python",
            source="manual",
            is_confirmed=True,
        )
        self.client.force_login(self.user)

    def _render_structure(self):
        response = self.client.get(reverse("dashboard:profile"))
        self.assertEqual(response.status_code, 200)
        parser = _StructureParser()
        parser.feed(response.content.decode())
        parser.close()
        return response, parser

    def test_profile_fields_skills_and_actions_share_one_continuous_form(self):
        response, parser = self._render_structure()
        main_layouts = [
            node for node in parser.root.descendants("div") if node.has_class("main-layout")
        ]
        self.assertEqual(len(main_layouts), 1)
        main_layout = main_layouts[0]

        forms = list(main_layout.descendants("form"))
        self.assertEqual(len(forms), 1)
        profile_form = forms[0]

        required_field_names = {
            "phone",
            "location",
            "linkedin_url",
            "current_level",
            "years_experience",
            "target_roles",
            "french_level",
            "english_level",
            "relocation_preference",
            "remote_preference",
            "skill_name",
            "remove_skill",
        }
        fields = list(profile_form.descendants("input")) + list(
            profile_form.descendants("select")
        ) + list(profile_form.descendants("textarea")) + list(
            profile_form.descendants("button")
        )
        rendered_names = {node.attrs.get("name") for node in fields}
        self.assertTrue(required_field_names.issubset(rendered_names))

        save_buttons = [
            node
            for node in profile_form.descendants("button")
            if node.attrs.get("data-en") == "Save profile"
        ]
        self.assertEqual(len(save_buttons), 1)
        self.assertNotIn("full_name", rendered_names)
        self.assertNotContains(response, 'name="full_name"')

    def test_progression_sidebar_is_form_sibling_inside_main_layout(self):
        _, parser = self._render_structure()
        main_layout = next(
            node for node in parser.root.descendants("div") if node.has_class("main-layout")
        )
        profile_form = next(main_layout.descendants("form"))
        sidebars = [
            node
            for node in main_layout.descendants("aside")
            if node.has_class("progression-aside")
        ]

        self.assertEqual(len(sidebars), 1)
        sidebar = sidebars[0]
        self.assertIs(sidebar.parent, main_layout)
        self.assertFalse(sidebar.is_descendant_of(profile_form))
        self.assertIs(profile_form.parent.parent, main_layout)

    def test_profile_page_has_balanced_expected_structure(self):
        _, parser = self._render_structure()

        self.assertEqual(parser.mismatches, [])
        self.assertEqual([node.tag for node in parser.stack], ["document"])
