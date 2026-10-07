import uvicorn


def main() -> None:
    uvicorn.run(
        "cloudheal_control_plane.api:app",
        host="0.0.0.0",
        port=9000,
        reload=False,
    )


if __name__ == "__main__":
    main()