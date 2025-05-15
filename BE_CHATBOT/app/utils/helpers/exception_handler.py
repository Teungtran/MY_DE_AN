from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.tracing import get_current_trace_ids


class ServiceName(str, Enum):
    """
    Enum for service names.
    """

    PREPROCESSING = "PRE"
    ORCHESTRATOR = "ORC"


class FunctionName(str, Enum):
    """
    Enum for function names.
    """

    CHANGEDETECTION = "CDE"
    DATA_PIPELINE = "DAP"
    RAG = "RAG"
    WORKFLOWs = "WFS"


class ErrorNumber(Enum):
    """
    Enum for error numbers.

    Each member corresponds to a specific error code suffix.
    """

    INTERNAL_SERVER_ERROR = "001"
    NOT_FOUND = "002"
    BAD_REQUEST = "003"
    UNPROCESSABLE_ENTITY = "004"
    # Additional error numbers can be added here
    # UNAUTHORIZED = "005"
    # FORBIDDEN = "006"


class CustomBaseModel(BaseModel):
    class Config:
        """Configuration of the Pydantic Object"""

        # Allowing arbitrary types for class validation
        arbitrary_types_allowed = True


def generate_error_code(service_name: str, function_name: str, error_number: ErrorNumber) -> str:
    """
    Generate a full error code by combining the service name, function name, and error number.

    Args:
        service_name (str): Identifier for the service (e.g. from ServiceName enum).
        function_name (str): Identifier for the function (e.g. from FunctionName enum).
        error_number (ErrorNumber): The error number enum member.

    Returns:
        str: The full error code in the format "SERVICE-FUNCTION-ERRORNUMBER".
    """
    return f"{service_name}-{function_name}-{error_number.value}"


class ExceptionHandler(CustomBaseModel):
    """
    ExceptionHandler provides methods to handle various error scenarios and generate
    standardized JSON responses that include error codes, HTTP status, messages, trace IDs,
    and additional extra data.
    """

    logger: Any
    service_name: ServiceName
    function_name: FunctionName

    def _create_response(
        self,
        error_code: str,
        message: str,
        status_code: int,
        success: bool,
        extra: Optional[Dict[str, Any]] = None,
        # trace_id: Optional[str] = None,
    ) -> JSONResponse:
        """
        Create a JSONResponse with a standardized error structure.

        The response format is:
            {
                "errorCode": <error_code>,
                "httpStatus": <status_code>,
                "message": <message>,
                "traceId": <trace_id>,
                "success": <success>,
                "data": <extra>
            }

        Args:
            error_code (str): The full error code.
            message (str): The error message (provided by parameter e).
            status_code (int): The HTTP status code.
            success (bool): Indicates whether the operation was successful.
            extra (Optional[Dict[str, Any]]): Additional extra data to include in the response.
            trace_id (Optional[str]): An optional trace ID for logging and tracking.

        Returns:
            JSONResponse: The JSON response object.
        """
        current_trace_id, _ = get_current_trace_ids()

        response_data = {
            "errorCode": error_code,
            "httpStatus": status_code,
            "message": message,
            "traceId": current_trace_id or "",
            "success": success,
            "data": extra or {},
        }
        return JSONResponse(content=response_data, status_code=status_code)

    def handle_exception(self, e: str, extra: Dict[str, Any]) -> JSONResponse:
        """
        Handle an internal server error exception.

        Args:
            e (str): The error message to be returned.
            extra (Dict[str, Any]): Extra information for logging, which is also returned in the data field.
            trace_id (Optional[str]): An optional trace ID.

        Returns:
            JSONResponse: The JSON response with error details.
        """
        self.logger.exception(e, extra=extra)
        full_error_code = generate_error_code(
            self.service_name.value, self.function_name.value, ErrorNumber.INTERNAL_SERVER_ERROR
        )
        return self._create_response(
            error_code=full_error_code,
            message=e,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            extra=extra,
        )

    def handle_not_found_error(self, e: str, extra: Dict[str, Any]) -> JSONResponse:
        """
        Handle a resource not found error.

        Args:
            e (str): The error message to be returned.
            extra (Dict[str, Any]): Extra information for logging, which is also returned in the data field.
            trace_id (Optional[str]): An optional trace ID.

        Returns:
            JSONResponse: The JSON response with error details.
        """
        self.logger.error(e, extra=extra)
        full_error_code = generate_error_code(self.service_name.value, self.function_name.value, ErrorNumber.NOT_FOUND)
        return self._create_response(
            error_code=full_error_code,
            message=e,
            status_code=status.HTTP_404_NOT_FOUND,
            success=False,
            extra=extra,
        )

    def handle_bad_request(self, e: str, extra: Dict[str, Any]) -> JSONResponse:
        """
        Handle a bad request error.

        Args:
            e (str): The error message to be returned.
            extra (Dict[str, Any]): Extra information for logging, which is also returned in the data field.
            trace_id (Optional[str]): An optional trace ID.

        Returns:
            JSONResponse: The JSON response with error details.
        """
        self.logger.error(e, extra=extra)
        full_error_code = generate_error_code(
            self.service_name.value, self.function_name.value, ErrorNumber.BAD_REQUEST
        )
        return self._create_response(
            error_code=full_error_code,
            message=e,
            status_code=status.HTTP_400_BAD_REQUEST,
            success=False,
            extra=extra,
        )

    def handle_unprocessable_entity(self, e: str, extra: Dict[str, Any]) -> JSONResponse:
        """
        Handle an unprocessable entity error.

        Args:
            e (str): The error message to be returned.
            extra (Dict[str, Any]): Extra information for logging, which is also returned in the data field.
            trace_id (Optional[str]): An optional trace ID.

        Returns:
            JSONResponse: The JSON response with error details.
        """
        self.logger.error(e, extra=extra)
        full_error_code = generate_error_code(
            self.service_name.value, self.function_name.value, ErrorNumber.UNPROCESSABLE_ENTITY
        )
        return self._create_response(
            error_code=full_error_code,
            message=e,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            success=False,
            extra=extra,
        )
