SHELL := /bin/zsh

PROJECT ?= samples/DuoSample
SCHEME ?= DuoSample
BUNDLE_ID ?= com.duopilot.sample
DERIVED_DATA ?= $(PROJECT)/.duopilot-derived
APP_PATH ?= $(DERIVED_DATA)/Build/Products/Debug-iphonesimulator/$(SCHEME).app
DUOPILOT ?= .venv/bin/duopilot

# Prefer a booted iPhone, otherwise select the first available iPhone.
DEVICE_ID ?= $(shell xcrun simctl list devices available 2>/dev/null | awk '/iPhone / && /Booted/ {for (i=1;i<=NF;i++) if ($$i ~ /^\([0-9A-F-]+\)$$/) {gsub(/[()]/,"",$$i); print $$i; exit}} /iPhone / && /Shutdown/ {for (i=1;i<=NF;i++) if ($$i ~ /^\([0-9A-F-]+\)$$/) {gsub(/[()]/,"",$$i); print $$i; exit}}')
DISPLAY ?= primary
SCREENSHOT_DELAY ?= 3

.PHONY: help setup doctor analyze fix build test boot run screenshot clean

help:
	@echo "DuoPilot commands:"
	@echo "  make setup       Install Python dependencies and generate the sample project"
	@echo "  make analyze     Inspect the sample without changing files"
	@echo "  make fix         Let the OpenAI agent edit, build and verify the sample"
	@echo "  make build       Build the sample for iOS Simulator"
	@echo "  make test        Run the sample unit tests on an iPhone Simulator"
	@echo "  make run         Build, boot, install and launch the sample"
	@echo "  make screenshot  Capture the primary display to $(PROJECT)/duopilot-screenshot.png"
	@echo ""
	@echo "Override PROJECT, SCHEME, BUNDLE_ID, DEVICE_ID, DISPLAY or SCREENSHOT_DELAY for another app/display."

setup:
	./setup.sh

doctor:
	@command -v xcodebuild >/dev/null || (echo "Xcode is required."; exit 1)
	@command -v xcrun >/dev/null || (echo "Xcode command-line tools are required."; exit 1)
	@test -x "$(DUOPILOT)" || (echo "DuoPilot is not installed. Run: make setup"; exit 1)
	@echo "Xcode: $$(xcodebuild -version | head -1)"
	@echo "DuoPilot: $$($(DUOPILOT) --help >/dev/null && echo ready)"
	@if [[ -n "$(DEVICE_ID)" ]]; then echo "Simulator: $(DEVICE_ID)"; else echo "Simulator: no available iPhone"; fi

analyze: doctor
	$(DUOPILOT) run $(PROJECT)

fix: doctor
	$(DUOPILOT) run $(PROJECT) --fix

build: doctor
	xcodebuild -project $(PROJECT)/$(SCHEME).xcodeproj -scheme $(SCHEME) \
		-sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
		-derivedDataPath $(DERIVED_DATA) CODE_SIGNING_ALLOWED=NO build

boot: doctor
	@if [[ -z "$(DEVICE_ID)" ]]; then echo "No available iPhone Simulator. Install an iOS runtime in Xcode."; exit 1; fi
	@xcrun simctl boot $(DEVICE_ID) >/dev/null 2>&1 || true
	@xcrun simctl bootstatus $(DEVICE_ID) -b

test: build boot
	xcodebuild -project $(PROJECT)/$(SCHEME).xcodeproj -scheme $(SCHEME) \
		-sdk iphonesimulator -destination 'id=$(DEVICE_ID)' \
		-derivedDataPath $(DERIVED_DATA) CODE_SIGNING_ALLOWED=NO test

run: build boot
	xcrun simctl install $(DEVICE_ID) $(APP_PATH)
	xcrun simctl launch $(DEVICE_ID) $(BUNDLE_ID)

screenshot: run
	@sleep $(SCREENSHOT_DELAY)
	xcrun simctl io $(DEVICE_ID) screenshot --display $(DISPLAY) $(PROJECT)/duopilot-screenshot.png
	@echo "Screenshot: $(PROJECT)/duopilot-screenshot.png"

clean:
	rm -rf $(DERIVED_DATA)
