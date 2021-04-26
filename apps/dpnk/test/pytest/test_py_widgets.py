from dpnk import widgets
from bs4 import BeautifulSoup


def test_render():
    """ Test render method """
    renderer = widgets.CommuteModeSelect(
        {},
        [
            (1, "Item 1"),
            (2, "Item 2"),
        ],
    )
    rendered_html = renderer.render(
        "test_name",
        1,
    )
    soup = BeautifulSoup(rendered_html, "html.parser")
    kids = soup.fieldset.children
    d1 = next(kids)
    assert d1.input.attrs["id"] == "id_test_name_1"
    assert d1.input.attrs["value"] == "1"
    assert d1.label.string == "Item 1"
    d2 = next(kids)
    assert d2.input.attrs["id"] == "id_test_name_2"
    assert d2.input.attrs["value"] == "2"
    assert d2.label.string == "Item 2"


def test_render_str():
    """ Test render method if the value is string and item int """
    renderer = widgets.CommuteModeSelect(
        {},
        [(1, "Item 1")],
    )
    rendered_html = renderer.render(
        "test name",
        "1",
    )
    soup = BeautifulSoup(rendered_html, "html.parser")
    assert len(list(soup.fieldset.children)) == 1
    assert soup.fieldset.div.input.attrs["value"] == "1"
    assert soup.fieldset.div.label.string == "Item 1"
