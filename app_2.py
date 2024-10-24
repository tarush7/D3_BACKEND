import json
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn

app = FastAPI(
    title="folder_data",
    description="Data for folder to generate graph",
    version="0.1.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with open('folder_data.json', 'r', encoding="utf8") as f:
    data = f.read()

class Relation(BaseModel):
    relation: str
    entities: List[str]
    status: str

class Profile(BaseModel):
    name: str
    relations: List[Relation]

class InputData(BaseModel):
    profile: List[Profile]
    status: List[str]
    has_person: str

def merge_dicts(dicts):
    merged = {}
    for d in dicts:
        for key, value in d.items():
            if key not in merged:
                merged[key] = value
            else:
                if isinstance(value, list):
                    merged[key].extend(value)
                elif isinstance(value, dict):
                    merged[key] = merge_dicts([merged[key], value])
                else:
                    merged[key] = value
    return merged

def merged_clean(data):
    filtered_profiles = {}
    for profile in data['profile']:
        name = profile['name']
        if name not in filtered_profiles:
            filtered_profiles[name] = {}
        # Only keep relations that have 'status' in {'Black', 'Blue'}
        filtered_relations = [relation for relation in profile['relations'] if relation['status'] in {'Black', 'Blue'}]
        if filtered_relations:  # Only process profiles with at least one valid relation
            for relation in filtered_relations:
                rel_type = relation['relation']
                if rel_type not in filtered_profiles[name]:
                    filtered_profiles[name][rel_type] = set()
                filtered_profiles[name][rel_type].update(relation['entities'])
    
    # Create a list of merged profiles, excluding empty relations
    merged_profiles = [
        {'name': name, 'relations': [{'relation': rel_type, 'entities': list(entities)} for rel_type, entities in relations.items()]}
        for name, relations in filtered_profiles.items() if relations
    ]
    
    filtered_data = {
        'profile': merged_profiles,
        'status': data['status'],
        'has_person': data['has_person']
    }
    
    return filtered_data

@app.get("/get_folder_data")
def health_check(response: Response):
    return json.loads(data)

@app.post("/get_merged_json/")
async def receive_json(data: List[InputData]):
    merged_dicts = merge_dicts([d.dict() for d in data])
    output_json = merged_clean(merged_dicts)
    return output_json

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=6969)