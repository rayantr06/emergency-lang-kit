# 💡 Example Use Cases

These examples demonstrate the structured JSON output produced by the ELK Kernel.

## Use Case 1: Fire Incident (High Confidence)

**Input Audio:** *"Allo, y'a le feu au troisième étage, rue de la Liberté!"* (French)

**Kernel Output:**
```json
{
  "call_id": "evt_2938472",
  "timestamp": "2026-05-12T14:30:00Z",
  "transcription": "Allo, y'a le feu au troisième étage, rue de la Liberté!",
  "intent": {
    "incident_type": "FIRE",
    "urgency": "CRITICAL"
  },
  "entities": {
    "location": {
      "type": "residence",
      "address": "Rue de la Liberté",
      "floor": 3
    },
    "hazards": ["smoke", "fire"]
  },
  "decision": {
    "action": "dispatch",
    "target": "Fire_Station_Central",
    "confidence": 0.98,
    "reasoning": "Keyword 'feu' aligned with FIRE enum. Urgency inferred from context 'troisième tage' (residential)."
  }
}
```

## Use Case 2: Code-Switching (Kabyle/French)

**Input Audio:** *"Urigh accident, yella daxel n tomobil, il respire mal."* 
*(Translation: "There is an accident, inside the car, he breathes badly.")*

**Kernel Output:**
```json
{
  "call_id": "evt_998877",
  "transcription": "Urigh accident, yella daxel n tomobil, il respire mal.",
  "intent": {
    "incident_type": "MEDICAL",
    "urgency": "HIGH"
  },
  "entities": {
    "casualties": 1,
    "condition": "respiratory_distress"
  },
  "decision": {
    "action": "dispatch",
    "target": "Ambulance_Unit_4",
    "confidence": 0.92,
    "reasoning": "Detected 'accident' (Mixed) and 'respire mal' (Medical). Priority raised due to breathing difficulty."
  }
}
```
