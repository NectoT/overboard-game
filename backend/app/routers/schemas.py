from fastapi import APIRouter
from pydantic import BaseModel
from pydantic.schema import schema

from .eventhandlers import playerevent


router = APIRouter(tags=["Schemas"], prefix="/schemas")


def add_schema_route(model: type[BaseModel]):
    '''Создаёт endpoint для получения схемы модели'''
    @router.get(
        '/' + model.__name__.lower(),
        name=f'Get {model.__name__} schema'
    )
    def fastapi_doc_route() -> dict:
        return model.schema()


player_events = [playerevent.handlers[name].event_type for name in playerevent.handlers]
for event in player_events:
    add_schema_route(event)

server_events: set[type[BaseModel]] = set()
for name in playerevent.handlers:
    server_events = server_events.union(set(playerevent.handlers[name].response_events))
for event in server_events:
    add_schema_route(event)



class EventSchemas(BaseModel):
    event_names: list[str]
    definitions: dict


@router.get('/playerevents')
def player_events_schemas() -> EventSchemas:
    schemas = schema(player_events)
    return EventSchemas(definitions=schemas, event_names=[e.__name__ for e in player_events])


@router.get('/serverevents')
def server_events_schemas() -> EventSchemas:
    schemas = schema(server_events)
    return EventSchemas(definitions=schemas, event_names=[e.__name__ for e in server_events])