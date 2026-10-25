from cloudheal_control_plane.database import (
    observe_incident,
    record_event,
    resolve_incident,
)
from cloudheal_control_plane.infrastructure.kubernetes_adapter import (
    get_deployment_status,
)
from cloudheal_control_plane.self_healing.detector import (
    detect_deployment_incident as _detect_deployment_incident,
)

def detect_deployment_incident(
    namespace: str,
    deployment_name: str,
) -> dict:

    return _detect_deployment_incident(
        namespace=namespace,
        deployment_name=deployment_name,
        get_deployment_status=get_deployment_status,
        observe_incident_fn=observe_incident,
        record_event_fn=record_event,
        resolve_incident_fn=resolve_incident,
    )
