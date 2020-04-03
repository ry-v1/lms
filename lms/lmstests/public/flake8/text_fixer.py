from lms.lmsdb import database_config
from lms.lmsdb import models
from lms.lmstests.sandbox.flake8 import defines


def fix_texts():
    with database_config.database.atomic():
        for flake8_key, text in defines.FLAKE_ERRORS_MAPPING.items():
            _fix_text(flake8_key, text)
            _join_flake8_errors(flake8_key)
        for flake8_key in defines.FLAKE_SKIP_ERRORS:
            _delete_comments_by_flake8_key(flake8_key)


def _join_flake8_errors(flake8_key: str) -> None:
    comments = models.CommentText.filter(
        models.CommentText.flake8_key == flake8_key,
    )
    try:
        primary = comments[0]
        extras = comments[1:]
    except IndexError:
        return
    for extra in extras:
        for comment in models.Comment.select().join(
                models.CommentText,
        ).filter(models.Comment.comment == extra):
            comment.comment = primary
            comment.save()
        extra.delete_instance()


def _fix_text(flake8_key: str, text: str) -> None:
    comments = models.CommentText.filter(models.CommentText.text == text)
    try:
        primary = comments[0]
        extras = comments[1:]
    except IndexError:
        return

    for extra in extras:
        for comment in models.Comment.select().filter(
                models.Comment.comment == extra,
        ):
            comment.comment = primary
            comment.save()
        extra.delete_instance()

    primary.text = text
    primary.flake8_key = flake8_key
    primary.save()


def _delete_comments_by_flake8_key(flake8_key: str) -> None:
    comments = models.CommentText.filter(
        models.CommentText.flake8_key == flake8_key,
    )
    for comment in comments:
        comments_to_delete = models.Comment.select().join(
            models.CommentText,
        ).filter(models.Comment.comment == comment)
        for comment_to_delete in comments_to_delete:
            comment_to_delete.delete_instance()
        comment.delete_instance()
