from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....core.security import get_current_user
from ....models.auth import Plot, PlotCreate, PlotResponse, PlotUpdate, User

router = APIRouter()


@router.post("/", response_model=PlotResponse, status_code=status.HTTP_201_CREATED)
def create_plot(
    plot_data: PlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlotResponse:
    """Create a new plot for the current user"""
    new_plot = Plot(
        title=plot_data.title,
        description=plot_data.description,
        plot_data=plot_data.plot_data,
        user_id=current_user.id,
    )
    db.add(new_plot)
    db.commit()
    db.refresh(new_plot)
    return PlotResponse.model_validate(new_plot)


@router.get("/", response_model=list[PlotResponse])
def get_user_plots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PlotResponse]:
    """Get all plots for the current user"""
    plots = db.query(Plot).filter(Plot.user_id == current_user.id).all()
    return [PlotResponse.model_validate(plot) for plot in plots]


@router.get("/{plot_id}", response_model=PlotResponse)
def get_plot(
    plot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlotResponse:
    """Get a specific plot by ID"""
    plot = db.query(Plot).filter(Plot.id == plot_id, Plot.user_id == current_user.id).first()
    if not plot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plot not found",
        )
    return PlotResponse.model_validate(plot)


@router.put("/{plot_id}", response_model=PlotResponse)
def update_plot(
    plot_id: int,
    plot_data: PlotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlotResponse:
    """Update a specific plot"""
    plot = db.query(Plot).filter(Plot.id == plot_id, Plot.user_id == current_user.id).first()
    if not plot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plot not found",
        )

    if plot_data.title is not None:
        plot.title = plot_data.title
    if plot_data.description is not None:
        plot.description = plot_data.description
    if plot_data.plot_data is not None:
        plot.plot_data = plot_data.plot_data

    db.commit()
    db.refresh(plot)
    return PlotResponse.model_validate(plot)


@router.delete("/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plot(
    plot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a specific plot"""
    plot = db.query(Plot).filter(Plot.id == plot_id, Plot.user_id == current_user.id).first()
    if not plot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plot not found",
        )

    db.delete(plot)
    db.commit()
