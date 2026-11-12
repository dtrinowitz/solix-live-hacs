# SOLIX Live Energiedashboard (Version 1.0.0)

Benutzerdefinierte Home-Assistant-Integration mit eigenem Sidebar-Panel und der freigegebenen V4.3-Hausansicht. Das Frontend enthält die Hausgrafik und animierte Lichtpunkte; Leistungswerte werden aus konfigurierten Home-Assistant-Sensoren gelesen, nicht simuliert.

## Installation über den Marketplace (Home Assistant 2026.11)

1. Home Assistant öffnen → **Marketplace**.
2. Falls noch nicht geschehen: **Benutzerdefinierte Repositorys** → **Über Link hinzufügen** → `https://github.com/dtrinowitz/solix-live-hacs` → Typ **Integration**.
3. Im Marketplace nach **SOLIX Live Energiedashboard** suchen und **Installieren** auswählen.
4. **Home Assistant neu starten**.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → **SOLIX Live Energiedashboard**.
6. Die tatsächlichen PV-, Ausgangsleistungs-, Ladezustands- und Smart-Plug-Entitäten beider Anlagen auswählen. Danach sollte **SOLIX Energie** in der Seitenleiste erscheinen.

Für ältere Home-Assistant-Versionen mit HACS ist der benutzerdefinierte Repository-Weg weiterhin möglich. Diese Anleitung beschreibt vorrangig den Marketplace, den Home Assistant 2026.11 auf der Zielinstallation anzeigt.

## Daten und Berechnungen

- **Solarleistung** = PV-System 1 + PV-System 2.
- **Ausgangsleistung** = Hausabgabe System 1 + Hausabgabe System 2.
- **Hausverbrauch** = Summe der ausgewählten Smart-Plug-Leistungssensoren.
- **Hauseinspeisung** = max(0, Ausgangsleistung − Hausverbrauch).
- **Ladestand** = ungewichteter Mittelwert der gewählten SoC-Sensoren.
- Nicht verfügbare Leistungswerte werden nicht durch Demo-Werte ersetzt. Gemessene PV-Werte werden auch nachts nicht künstlich auf null gesetzt.

Die Hauseinspeisung ist eine **berechnete Restleistung**, keine Messung eines Netz-Zweirichtungszählers. Die Integration steuert keine Anker-Geräte.

## Hinweise zur Konfiguration

Die vorgeschlagenen Entity-IDs im Einrichtungsdialog sind lediglich Beispiele. Prüfe vor dem Speichern, dass die beiden Anlagen tatsächlich unterschiedlichen Entitäten zugeordnet sind und die Smart-Plug-Auswahl nur **aktuelle Leistungssensoren (W/kW)** enthält, keine kumulierten Energiesensoren (Wh/kWh). Automatische, zweifelsfreie Erkennung ist noch nicht implementiert.

Die grafische Ansicht ist in `custom_components/solix_live/frontend/solix-live-panel.js` eingebettet; keine separate Bilddatei oder manuelle Lovelace-JavaScript-Ressource erforderlich.

## Stand und Einschränkungen

Die Dateien sind im GitHub-Repository vorhanden. Ein erfolgreicher Marketplace-Eintrag bestätigt die Erkennung des Repositorys, **nicht** die Laufzeitfunktion. Ein vollständiger Live-Test auf der Zielinstallation steht noch aus. Vor dem produktiven Einsatz sind Einrichtung, Sidebar-Anzeige, Sensorberechnung und Animation zu prüfen.

Projekt: https://github.com/dtrinowitz/solix-live-hacs
