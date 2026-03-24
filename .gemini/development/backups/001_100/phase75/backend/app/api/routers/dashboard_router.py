from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from db.database import get_db
from backend.app.services.dashboard_service import DashboardService
from backend.app.utils.error_handler import handle_agent_errors
from backend.app.services.search_service import SearchService
from backend.app.services.opportunity_service import OpportunityService
from backend.app.core.templates import templates
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
@handle_agent_errors
async def dashboard_view(request: Request, db: Session = Depends(get_db)):
    try:
        logger.debug("Entering dashboard endpoint")
        data = DashboardService.get_dashboard_data(db)
        
        return templates.TemplateResponse(request, "dashboard/dashboard.html", {
            "request": request, 
            **data
        })
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return RedirectResponse(url="/leads?error=Error+loading+dashboard")

@router.get("/api/recommendations")
async def get_ai_recommendations(request: Request, db: Session = Depends(get_db)):
    try:
        from ai_agent.backend.recommendations import AIRecommendationService
        recommended_opps = AIRecommendationService.get_ai_recommendations(db, limit=5)
        current_mode = AIRecommendationService.CURRENT_MODE
        
        # Pre-fetch model names for the fragment
        from backend.app.services.model_service import ModelService
        for opp in recommended_opps:
            model = ModelService.get_model(db, opp.model) if opp.model else None
            opp.model_name = model.name if model else "-"
            
        return templates.TemplateResponse(request, "dashboard/dashboard_ai_recommend_fragment.html", {
            "request": request,
            "recommended_opportunities": recommended_opps,
            "recommendation_mode": current_mode
        })
    except Exception as e:
        logger.error(f"AI recommendations error: {e}")
        return HTMLResponse(
            content=f'<div class="sf-card" style="padding:1rem;color:var(--error);text-align:center;">'
                    f'Unable to load recommendations at this time: {str(e)}</div>',
            status_code=200 # Return 200 so JS doesn't trigger global error redirect
        )


@router.get("/api/search/suggestions")
async def get_search_suggestions(q: str = "", type: str = "all", db: Session = Depends(get_db)):
    try:
        results = SearchService.global_search(db, q, type, limit=8)
        return results
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        return []

@router.get("/search")
async def global_search(request: Request, q: str = "", type: str = "all", db: Session = Depends(get_db)):
    try:
        logger.debug(f"Entering global_search endpoint with query: {q}, type: {type}")
        results = SearchService.global_search(db, q, type)
        return templates.TemplateResponse(request, "search_results.html", {"request": request, "query": q, "results": results})
    except Exception as e:
        logger.error(f"Global search error: {e}")
        return templates.TemplateResponse(request, "search_results.html", {"request": request, "query": q, "results": [], "error": str(e)})
