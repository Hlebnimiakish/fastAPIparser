"""This module contains basic exception raiser function for FastAPI path operation functions"""

from fastapi import HTTPException


def unpredicted_exception_raising(data):
    """Tries to return passed in data on fail raises exception"""
    try:
        return data
    except ConnectionError as conner:
        raise HTTPException(status_code=408, detail=str(conner)) from conner
    except TimeoutError as tierr:
        raise HTTPException(status_code=408, detail=str(tierr)) from tierr
    except ValueError as verr:
        raise HTTPException(status_code=400, detail=str(verr)) from verr
    except TypeError as terr:
        raise HTTPException(status_code=415, detail=str(terr)) from terr
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
