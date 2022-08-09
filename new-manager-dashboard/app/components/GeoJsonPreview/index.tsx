import React from 'react';
import {
    map as createMap,
    Map,
    tileLayer,
    geoJSON,
    GeoJSON as LeafletGeoJSON,
} from 'leaflet';
import { _cs } from '@togglecorp/fujs';

import styles from './styles.css';

interface Props {
    className?: string;
    geoJson: GeoJSON.GeoJSON | undefined;
}

function GeoJsonPreview(props: Props) {
    const {
        className,
        geoJson,
    } = props;

    const mapRef = React.useRef<Map>();
    const mapContainerRef = React.useRef<HTMLDivElement>(null);
    const geoJsonLayerRef = React.useRef<LeafletGeoJSON>();

    React.useEffect(
        () => {
            if (mapContainerRef.current && !mapRef.current) {
                mapRef.current = createMap(mapContainerRef.current);
            }

            if (mapRef.current) {
                // NOTE: show whole world by default
                mapRef.current.setView(
                    [0.0, 0.0],
                    1,
                );

                const layer = tileLayer(
                    'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    {
                        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                        subdomains: ['a', 'b', 'c'],
                    },
                );

                layer.addTo(mapRef.current);
                mapRef.current.invalidateSize();
            }

            return () => {
                if (mapRef.current) {
                    mapRef.current.remove();
                    mapRef.current = undefined;
                }
            };
        },
        [],
    );

    React.useEffect(
        () => {
            if (!geoJson) {
                return undefined;
            }

            if (!mapRef.current) {
                return undefined;
            }

            if (mapRef.current) {
                const newGeoJson = geoJSON();
                geoJsonLayerRef.current = newGeoJson;
                newGeoJson.addTo(mapRef.current);

                newGeoJson.addData(geoJson);
                const bounds = newGeoJson.getBounds();

                if (bounds.isValid()) {
                    mapRef.current.fitBounds(bounds);
                }
            }

            return () => {
                if (geoJsonLayerRef.current && mapRef.current) {
                    geoJsonLayerRef.current.removeFrom(mapRef.current);
                    geoJsonLayerRef.current.remove();
                    geoJsonLayerRef.current = undefined;
                }
            };
        },
        [geoJson],
    );

    return (
        <div className={_cs(styles.geoJsonPreview, className)}>
            <div
                ref={mapContainerRef}
                className={styles.mapContainer}
            />
        </div>
    );
}

export default GeoJsonPreview;
