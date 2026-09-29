from sqlalchemy.orm import Session, selectinload

from app.models import Tag, Task


def list_tasks(db: Session) -> list[Task]:
    # selectinload로 태그를 한 번에 가져옵니다.
    # 즉시 로딩하지 않으면 직렬화 시 task.tags 접근마다 쿼리가 발생해(N+1)
    # 할 일이 늘수록 GET /tasks 가 느려집니다.
    tasks = db.query(Task).options(selectinload(Task.tags)).all()
    return tasks


def get_task(db: Session, task_id: int) -> Task | None:
    # 단건이지만 TaskOut이 tags를 직렬화하므로 여기서도 eager 로딩을 붙입니다.
    return (
        db.query(Task)
        .options(selectinload(Task.tags))
        .filter(Task.id == task_id)
        .first()
    )


def create_task(db: Session, title: str, tag_names: list[str]) -> Task:
    tags: list[Tag] = []
    for name in tag_names:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
        tags.append(tag)

    task = Task(title=title, tags=tags)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
