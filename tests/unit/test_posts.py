import pytest

from app.domain import models
from app.domain import exceptions


def test_create_post_with_valid_images_number():
    images = [model.Image(original='img.jpg') for _ in range(10)]
    post = model.Post(user_id=1, title="title", description="description", images=images)
    assert post.image_number == 10


def test_create_post_with_zero_images_number_exception():
    with pytest.raises(exceptions.ImageNumberLimit):
        model.Post(user_id=1, title="title", description="description", images=[])


def test_create_post_with_images_number_limit_exception():
    with pytest.raises(exceptions.ImageNumberLimit):
        model.Post(
            user_id=1,
            title="title",
            description="description",
            images=[model.Image(original='img.jpg') for _ in range(12)]
        )


def test_delete_last_image_in_post():
    image = model.Image(original='img.jpg')
    post = model.Post(
        user_id=1,
        title="title",
        description="description",
        images=[image]
    )
    with pytest.raises(exceptions.ImageNumberLimit):
        post.delete_image(image)


def test_attach_more_then_limit_number_of_images():
    image = model.Image(original='img.jpg')
    post = model.Post(
        user_id=1,
        title="title",
        description="description",
        images=[image]
    )
    with pytest.raises(exceptions.ImageNumberLimit):
        post.attach_images([model.Image(original='img.jpg') for _ in range(12)])
