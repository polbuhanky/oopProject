from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from enum import Enum


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    project_id: Optional[UUID] = None


class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    username: str
    email: str


class TaskRepository:
    def __init__(self):
        self._tasks: Dict[UUID, Task] = {}

    def get_all(self) -> List[Task]:
        return list(self._tasks.values())

    def get_by_id(self, task_id: UUID) -> Optional[Task]:
        return self._tasks.get(task_id)

    def create(self, task: Task) -> Task:
        self._tasks[task.id] = task
        return task

    def update(self, task: Task) -> Task:
        if task.id not in self._tasks:
            raise ValueError("Task not found")
        self._tasks[task.id] = task
        return task

    def delete(self, task_id: UUID) -> None:
        if task_id not in self._tasks:
            raise ValueError("Task not found")
        del self._tasks[task_id]

    def get_by_project(self, project_id: UUID) -> List[Task]:
        return [task for task in self._tasks.values() if task.project_id == project_id]


class ProjectRepository:
    def __init__(self):
        self._projects: Dict[UUID, Project] = {}

    def get_all(self) -> List[Project]:
        return list(self._projects.values())

    def get_by_id(self, project_id: UUID) -> Optional[Project]:
        return self._projects.get(project_id)

    def create(self, project: Project) -> Project:
        self._projects[project.id] = project
        return project

    def update(self, project: Project) -> Project:
        if project.id not in self._projects:
            raise ValueError("Project not found")
        self._projects[project.id] = project
        return project

    def delete(self, project_id: UUID) -> None:
        if project_id not in self._projects:
            raise ValueError("Project not found")
        del self._projects[project_id]


class UserRepository:
    def __init__(self):
        self._users: Dict[UUID, User] = {}

    def get_all(self) -> List[User]:
        return list(self._users.values())

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self._users.get(user_id)

    def create(self, user: User) -> User:
        self._users[user.id] = user
        return user

    def update(self, user: User) -> User:
        if user.id not in self._users:
            raise ValueError("User not found")
        self._users[user.id] = user
        return user

    def delete(self, user_id: UUID) -> None:
        if user_id not in self._users:
            raise ValueError("User not found")
        del self._users[user_id]


task_repo = TaskRepository()
project_repo = ProjectRepository()
user_repo = UserRepository()

app = FastAPI()


def validate_task_exists(task_id: UUID):
    task = task_repo.get_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


def validate_project_exists(project_id: UUID):
    project = project_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


def validate_user_exists(user_id: UUID):
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@app.post("/tasks/", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: Task):
    if task.project_id and not project_repo.get_by_id(task.project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project not found"
        )
    return task_repo.create(task)


@app.get("/tasks/", response_model=List[Task])
def list_tasks():
    return task_repo.get_all()


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: UUID):
    return validate_task_exists(task_id)


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: UUID, task: Task):
    if task_id != task.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task ID mismatch"
        )
    validate_task_exists(task_id)
    if task.project_id and not project_repo.get_by_id(task.project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project not found"
        )
    return task_repo.update(task)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID):
    validate_task_exists(task_id)
    task_repo.delete(task_id)


@app.patch("/tasks/{task_id}/status", response_model=Task)
def update_task_status(task_id: UUID, status: TaskStatus):
    task = validate_task_exists(task_id)
    task.status = status
    return task_repo.update(task)


@app.post("/projects/", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(project: Project):
    return project_repo.create(project)


@app.get("/projects/", response_model=List[Project])
def list_projects():
    return project_repo.get_all()


@app.get("/projects/{project_id}", response_model=Project)
def get_project(project_id: UUID):
    return validate_project_exists(project_id)


@app.get("/projects/{project_id}/tasks", response_model=List[Task])
def get_project_tasks(project_id: UUID):
    validate_project_exists(project_id)
    return task_repo.get_by_project(project_id)


@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID):
    validate_project_exists(project_id)
    for task in task_repo.get_by_project(project_id):
        task_repo.delete(task.id)
    project_repo.delete(project_id)


@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: User):
    return user_repo.create(user)


@app.get("/users/", response_model=List[User])
def list_users():
    return user_repo.get_all()


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: UUID):
    return validate_user_exists(user_id)
