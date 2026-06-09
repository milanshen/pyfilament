image-base:
	podman build -f Dockerfile -t pyfilament/filament-base:dev-latest .

image-ui:
	podman build -f ui/Dockerfile -t pyfilament/ui:dev-latest ui
