## TypeScript generation tests

The TypeScript integration tests need a local, built checkout of the vehicle-app TypeScript SDK. Use Node.js 20 or newer and npm. If the SDK checkout does not have build output yet, install and build it first:

```bash
cd /path/to/vehicle-app-ts-sdk
npm install
npm run build
```

Then run the TypeScript generator and model tests from this repository's root, setting `VEHICLE_APP_TS_SDK_PATH` to the SDK checkout:

```bash
cd /path/to/vehicle-model-generator
VEHICLE_APP_TS_SDK_PATH=/path/to/vehicle-app-ts-sdk \
  python -m pytest tests/test_typescript_generator.py tests/test_model_generator.py -k typescript
```

The test setup temporarily maps the local SDK to the generated model's `vehicle-app-ts-sdk` import name and restores the generated `package.json` afterward. 
If `VEHICLE_APP_TS_SDK_PATH` is unset, SDK-dependent integration tests are skipped.