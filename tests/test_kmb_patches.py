"""Stdlib-only checks that the local patches are still in place and still behave.

Home Assistant is not installed in CI for this repo, so the functions under test are
extracted from the source with `ast` and run against a minimal set of constants.
Run: python -m unittest discover tests
"""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "blueiris"


def _function(path: pathlib.Path, class_name: str, func_name: str) -> ast.FunctionDef:
    tree = ast.parse(path.read_text())
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name):
        for fn in cls.body:
            if isinstance(fn, ast.FunctionDef) and fn.name == func_name:
                return fn
    raise AssertionError(f"{class_name}.{func_name} not found in {path.name}")


def _load_is_online():
    fn = _function(ROOT / "api" / "blue_iris_api.py", "BlueIrisApi", "_is_online")
    fn.decorator_list = []
    ns = {
        "Any": object,
        "BI_ATTR_ID": "optionValue",
        "BI_ATTR_IS_ONLINE": "isOnline",
        "BI_ATTR_IS_ENABLED": "isEnabled",
        "BI_CAMERA_TYPE_GROUP": 99,
        "BI_CAMERA_TYPE_SYSTEM": 98,
    }
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "is_online", "exec"), ns)
    return ns["_is_online"], ns


class IsOnline(unittest.TestCase):
    def setUp(self):
        self.fn, self.ns = _load_is_online()

    def test_cycle_view_without_isonline_follows_isenabled(self):
        self.assertTrue(self.fn({"optionValue": "@Wallpanel", "isEnabled": True}, 4))
        self.assertFalse(self.fn({"optionValue": "@Wallpanel", "isEnabled": False}, 4))

    def test_cycle_view_with_isonline_is_untouched(self):
        self.assertFalse(self.fn({"optionValue": "@x", "isOnline": False, "isEnabled": True}, 4))

    def test_regular_camera_unchanged(self):
        self.assertTrue(self.fn({"optionValue": "Front", "isOnline": True}, 4))
        self.assertFalse(self.fn({"optionValue": "Front", "isOnline": False, "isEnabled": True}, 4))
        self.assertFalse(self.fn({"optionValue": "Front", "isEnabled": True}, 4))

    def test_group_and_system_still_use_isenabled(self):
        self.assertTrue(self.fn({"optionValue": "Wallpanel", "isEnabled": True}, self.ns["BI_CAMERA_TYPE_GROUP"]))


class FrameInterval(unittest.TestCase):
    def test_floor_is_ten_fps(self):
        src = (ROOT / "camera.py").read_text()
        tree = ast.parse(src)
        floor = next(
            n.value.value
            for n in tree.body
            if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "MIN_POLL_FPS"
        )
        self.assertGreaterEqual(floor, 10)
        fn = _function(ROOT / "camera.py", "BlueIrisCamera", "frame_interval")
        self.assertIn("MIN_POLL_FPS", ast.unparse(fn))


if __name__ == "__main__":
    unittest.main()
