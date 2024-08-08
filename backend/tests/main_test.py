import os
from uuid import uuid4


def test_apply_transparency(client):
    data = [
        {
            "image": "wikipedia-logo.png",
            "color": [255, 255, 255],
        },
        {
            "image": "pic.jpg",
            "color": [255, 255, 255],
        },
    ]
    for d in data:
        response = client.post("/apply-transparency", json=d)
        assert response.status_code == 200

        assert "file_name" in response.json, response.json
        assert "file_url" in response.json, response.json



def test_get_image_center(client):
    data = {
        # 'image': 'wikipedia-logo.png',
        "image": "tetraedro.png"
    }
    response = client.post("/get-image-center", json=data)
    assert response.status_code == 200, response.json
    assert "center" in response.json, response.json


def test_upload_image_no_selected_file(client):
    # get tests/ path
    path = os.path.dirname(os.path.abspath(__file__))

    # send tests/data/center_tetraedro.jpg as formdata file
    file_path = f"{path}/data/center_tetraedro.jpg"

    uuid = str(uuid4())
    data = {"image": (file_path, f"{uuid}_tetraedro.jpg", "image/jpeg")}

    response = client.post("/upload", data=data, content_type="multipart/form-data")

    assert response.status_code == 200
    assert "file_url" in response.json
    assert "file_name" in response.json, response.json
