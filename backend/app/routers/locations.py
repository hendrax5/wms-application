from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationUpdate, LocationRead

router = APIRouter(prefix="/api/locations", tags=["Locations"])


@router.get("/", response_model=list[LocationRead])
def list_locations(
    type: str | None = None,
    customer_id: int | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Location)
    if type:
        query = query.filter(Location.type == type)
    if customer_id:
        query = query.filter(Location.customer_id == customer_id)
    if is_active is not None:
        query = query.filter(Location.is_active == is_active)
    if search:
        query = query.filter(
            (Location.name.ilike(f"%{search}%")) |
            (Location.city.ilike(f"%{search}%")) |
            (Location.address.ilike(f"%{search}%"))
        )
    locations = query.order_by(Location.name).all()

    results = []
    for loc in locations:
        r = LocationRead.model_validate(loc)
        r.customer_name = loc.customer.name if loc.customer else None
        r.parent_name = loc.parent.name if loc.parent else None
        r.device_count = len(loc.devices_here) if loc.devices_here else 0
        results.append(r)
    return results


@router.get("/{location_id}", response_model=LocationRead)
def get_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    r = LocationRead.model_validate(loc)
    r.customer_name = loc.customer.name if loc.customer else None
    r.parent_name = loc.parent.name if loc.parent else None
    r.device_count = len(loc.devices_here) if loc.devices_here else 0
    return r


@router.post("/", response_model=LocationRead)
def create_location(data: LocationCreate, db: Session = Depends(get_db)):
    loc = Location(**data.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)
    r = LocationRead.model_validate(loc)
    r.customer_name = loc.customer.name if loc.customer else None
    r.parent_name = loc.parent.name if loc.parent else None
    return r


@router.put("/{location_id}", response_model=LocationRead)
def update_location(location_id: int, data: LocationUpdate, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(loc, key, val)
    db.commit()
    db.refresh(loc)
    r = LocationRead.model_validate(loc)
    r.customer_name = loc.customer.name if loc.customer else None
    r.parent_name = loc.parent.name if loc.parent else None
    return r


@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)):
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    if loc.devices_here:
        raise HTTPException(status_code=400, detail="Cannot delete location with devices")
    db.delete(loc)
    db.commit()
    return {"detail": "Deleted"}
