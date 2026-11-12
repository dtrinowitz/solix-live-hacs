# SOLIX Live Energiedashboard 1.0.0

Home-Assistant-Custom-Integration mit eigenem Sidebar-Panel, originalem freigegebenem V4.3-Hausmotiv und kontinuierlichen Lichtpunktanimationen. **Keine Demo- oder Zufallswerte.**

## HACS-Installation

1. In HACS das öffentliche Repository `https://github.com/dtrinowitz/solix-live-hacs` als benutzerdefiniertes Repository hinzufügen (Kategorie **Integration**).
2. Die Integration **SOLIX Live Energiedashboard** in HACS herunterladen.
3. Home Assistant neu starten. Einstellungen → Geräte & Dienste → Integration hinzufügen → **SOLIX Live Energiedashboard**.
4. Live-Sensoren in der Oberfläche auswählen. Danach erscheint **SOLIX Energie** links in der Seitenleiste. Keine manuelle JavaScript-Ressource oder YAML notwendig.

## Vorgeschlagene Entity-IDs (vor Ort in Home Assistant prüfen)

| Funktion | System 1 | System 2 |
|---|---|---|
| PV | `sensor.solarbank_2_e1600_pro_solarleistung` | `sensor.solarbank_2_e1600_pro_solarleistung_2` |
| Ausgang | `sensor.solarbank_2_e1600_pro_ac_hausabgabe` | `sensor.solarbank_2_e1600_pro_ac_hausabgabe_2` |
| SoC | `sensor.solarbank_2_e1600_pro_ladestand` | `sensor.solarbank_2_e1600_pro_ladestand_2` |
| Status | `sensor.solarbank_2_e1600_pro_betriebszustand` | `sensor.solarbank_2_e1600_pro_betriebszustand_2` |

Bekannter Smart Plug: `sensor.smart_plug_leistung`. Weitere Smart-Plug-Sensoren in der Mehrfachauswahl hinzufügen. Die zwei Pro-Geräte müssen in Home Assistant als tatsächlich unterschiedliche Anlagen bestätigt werden; `_2` allein ist kein sicherer Beweis.

**Berechnung:** PV = Summe beider Pro-PV-Sensoren; Ausgang = Summe beider AC-Hausabgaben; Hausverbrauch = Summe der gewählten Smart-Plug-Leistungen; Hauseinspeisung = max(0, Ausgang − Hausverbrauch). Nicht verfügbare Werte bleiben unbekannt (keine simulierten Nullwerte). Ladezustand = einfacher Mittelwert der zwei gewählten SoC-Sensoren, nicht kapazitätsgewichtet.

**Wichtig:** Diese erste Integration enthält noch keine automatische, zweifelsfreie Zuordnung der Anlagen und Smart Plugs. Die Auswahl geschieht über Home Assistant ohne Codeeingriff. Die ursprüngliche V4.3-Grafik ist enthalten. Kein Live-Test auf deiner HA-Installation durchgeführt.

## Veröffentlichungsstand

Repository: https://github.com/dtrinowitz/solix-live-hacs

Quellcode ist veröffentlicht; die Installation und Sensorwerte wurden noch nicht in einer echten Home-Assistant-Instanz geprüft. Das große Frontend-Motiv bleibt unverändert.
