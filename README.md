# SOLIX Live Energiedashboard (Version 1.1.0)

Benutzerdefinierte Home-Assistant-Integration mit eigenem Sidebar-Panel und der freigegebenen V4.3-Hausansicht. Das Frontend enthält die Hausgrafik und animierte Lichtpunkte; Leistungswerte werden aus konfigurierten Home-Assistant-Sensoren gelesen, nicht simuliert.

## Installation über den Marketplace (Home Assistant 2026.11)

1. Home Assistant öffnen → **Marketplace**.
2. Falls noch nicht geschehen: **Benutzerdefinierte Repositorys** → **Über Link hinzufügen** → `https://github.com/dtrinowitz/solix-live-hacs` → Typ **Integration**.
3. Im Marketplace nach **SOLIX Live Energiedashboard** suchen und **Installieren** auswählen.
4. **Home Assistant neu starten**.
5. **Einstellungen → Geräte & Dienste → Integration hinzufügen** → **SOLIX Live Energiedashboard**.
6. Die tatsächlichen PV-, Ausgangsleistungs-, Ladezustands- und Smart-Plug-Entitäten beider Anlagen auswählen. Für die vier Hauptgeräte (2 × Solarbank 2 Pro, 2 × E1600) sowie die acht MPPT-Eingänge stehen zusätzliche **optionale** Sensorfelder bereit. Falls die Sensoren nicht vorhanden sind, die Felder leer lassen. Danach sollte **SOLIX Energie** in der Seitenleiste erscheinen.

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

## Neu in 1.1.0

- Ein defekter Smart-Plug blockiert die Hausverbrauchsberechnung nicht mehr; fehlende Steckdosen werden als unvollständige Daten in den Sensorattributen kenntlich gemacht.
- PV- und AC-Ausgangsquellen werden bei Teilausfall unabhängig ausgewertet; fehlende Quellen sind in Attributen sichtbar.
- Unter dem unveränderten Hausmotiv erscheinen vier Batterie-Karten mit Temperatur, Ladestand und Lade-/Entladeleistung, soweit zugeordnet und verfügbar.
- MPPT-Eingänge (vier je Pro-System) und Smart-Plugs erscheinen in aufklappbaren Detailbereichen.
- **Einrichtung bestehender Installation:** Nach Marketplace-Update unter Einstellungen → Geräte & Dienste → SOLIX Live → Konfigurieren die neuen optionalen Felder belegen. Sensor-IDs nicht erraten: tatsächliche Entitäten aus Home Assistant auswählen.
- Die Leistungsanzeige bei nicht verfügbaren Steckdosen ist eine **Teilsumme**, keine garantierte Gesamtmessung. Die errechnete Hauseinspeisung ist dann ebenfalls nur eingeschränkt aussagekräftig.
- GitHub Actions führt eine grundlegende Python-, JSON- und JavaScript-Syntaxprüfung aus; ein Live-Funktionstest auf Home Assistant ist weiterhin erforderlich.
