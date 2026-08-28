from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from lunar_python import Solar

app = FastAPI()


class SajuRequest(BaseModel):
    year: int
    month: int
    day: int
    time: str
    gender: str
    birthplace: str


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "my-saju-api",
        "version": "1.0"
    }


@app.post("/calculateSajuChart")
def calculate_saju_chart(data: SajuRequest):
    try:
        hour, minute = map(int, data.time.split(":"))

        solar = Solar.fromYmdHms(
            data.year,
            data.month,
            data.day,
            hour,
            minute,
            0
        )

        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        result = {
            "yearPillar": eight_char.getYear(),
            "monthPillar": eight_char.getMonth(),
            "dayPillar": eight_char.getDay(),
            "hourPillar": eight_char.getTime()
        }

        return {
            "ok": True,
            "input": {
                "year": data.year,
                "month": data.month,
                "day": data.day,
                "time": data.time,
                "gender": data.gender,
                "birthplace": data.birthplace
            },
            "chart": result
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
