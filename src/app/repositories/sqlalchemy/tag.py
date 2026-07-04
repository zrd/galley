from uuid import UUID

from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import TagModel, ManuscriptTagModel
from app.domain import Tag

from ._mappers import tag_model_to_domain


class TagRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, tag: Tag) -> Tag:
        model = TagModel(
            id=tag.id,
            name=tag.name,
            slug=tag.slug,
            owner_id=tag.owner_id,
            created_at=tag.created_at,
            deleted_at=tag.deleted_at,
        )
        self.session.add(model)
        self.session.flush()
        return tag_model_to_domain(model)

    def get(self, tag_id: UUID) -> Tag | None:
        stmt = select(TagModel).where(TagModel.id == tag_id)
        model = self.session.scalars(stmt).one_or_none()
        if model is None:
            return None
        return tag_model_to_domain(model)

    def list_by_owner(self, owner_id: UUID) -> list[Tag]:
        stmt = select(TagModel).where(TagModel.owner_id == owner_id).order_by(TagModel.name)
        models = self.session.scalars(stmt).all()
        return [tag_model_to_domain(m) for m in models]

    def update(self, tag: Tag) -> Tag:
        model = self.session.get(TagModel, tag.id)
        if model:
            model.name = tag.name
            model.slug = tag.slug
            model.owner_id = tag.owner_id
            model.created_at = tag.created_at
            model.deleted_at = tag.deleted_at
            self.session.flush()
            return tag_model_to_domain(model)
        raise ValueError(f"Tag {tag.id} not found")

    def get_by_slug(self, slug: str, owner_id: UUID) -> Tag | None:
        stmt = select(TagModel).where(TagModel.slug == slug, TagModel.owner_id == owner_id)
        model = self.session.scalars(stmt).one_or_none()
        if model is None:
            return None
        return tag_model_to_domain(model)

    def get_or_create(self, name: str, owner_id: UUID) -> Tag:
        slug = slugify(name)
        tag = self.get_by_slug(slug, owner_id)
        if tag is None:
            tag = self.add(Tag(
                name=name,
                slug=slug,
                owner_id=owner_id,
            ))
        elif tag.is_deleted:
            tag.restore()
            tag = self.update(tag)

        return tag

    def list_popular(self, top_n: int) -> list[Tag]:
        stmt = (
            select(TagModel, func.count(ManuscriptTagModel.manuscript_id).label("usage_count"))
            .join(ManuscriptTagModel, ManuscriptTagModel.tag_id == TagModel.id, isouter=True)
            .where(TagModel.deleted_at.is_(None))
            .group_by(TagModel.id)
            .order_by(func.count(ManuscriptTagModel.manuscript_id).desc())
            .limit(top_n)
        )
        rows = self.session.execute(stmt).all()
        return [tag_model_to_domain(row.TagModel) for row in rows]

    def list_all(self) -> list[Tag]:
        stmt = (
            select(TagModel, func.count(ManuscriptTagModel.manuscript_id).label("usage_count"))
            .join(ManuscriptTagModel, ManuscriptTagModel.tag_id == TagModel.id, isouter=True)
            .where(TagModel.deleted_at.is_(None))
            .group_by(TagModel.id)
            .order_by(func.count(ManuscriptTagModel.manuscript_id).desc())
        )
        rows = self.session.execute(stmt).all()
        return [tag_model_to_domain(row.TagModel) for row in rows]
