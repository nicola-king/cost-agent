from app.services.capability import CapabilityManifest, CapabilityResult, gateway

def register(manifest: CapabilityManifest):
    def deco(fn):
        gateway.register(manifest, fn)
        return fn
    return deco
