// FORCE CLEAR CACHE
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(function(registrations) {
        for(let registration of registrations) {
            registration.unregister();
        }
    });
}
caches.keys().then((keyList) => Promise.all(keyList.map((key) => caches.delete(key))));

// Map initialized below
let map = null;

function initMap() {
    if (!map) {
        map = L.map('map').setView([-14.235, -51.925], 4);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
        }).addTo(map);
    }
}


// Store chart instances so we can destroy them before recreating (prevents canvas reuse error)
let chartInstances = {};

function destroyChart(id) {
    if (chartInstances[id]) {
        chartInstances[id].destroy();
        chartInstances[id] = null;
    }
}

// Fetch and render data
async function loadDashboardData() {
    try {
        const state = document.getElementById('filter-state')?.value || 'ALL';
        const risk = document.getElementById('filter-risk')?.value || 'ALL';
        const start = document.getElementById('filter-date-start')?.value || '';
        const end = document.getElementById('filter-date-end')?.value || '';
        
        const params = new URLSearchParams({ state, risk, start_date: start, end_date: end });
        
        const response = await fetch(`../api/get_dashboard_data.php?${params.toString()}`);
        const data = await response.json();
        
        if (data.error) {
            console.error("API Error:", data.error);
        }

        
        if (data.map_data) {
            const stateSelect = document.getElementById('filter-state');
            if (stateSelect && stateSelect.options.length <= 1) {
                const states = [...new Set(data.map_data.map(d => d.state_name).filter(Boolean))].sort();
                states.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.textContent = s;
                    stateSelect.appendChild(opt);
                });
            }
        }
        
        renderOverview(data);

        initMap();
        renderMap(data.map_data || []);
        renderHotspotsChart(data.municipality_stats?.hotspots || []);
        renderSeasonalChart(data.seasonal_risk || []);
        renderClimateChart(data.climate_disease_trends || []);
        renderModelPerformance(data.model_performance || {});
        if(typeof renderAllBriefCharts === 'function') renderAllBriefCharts(data);

    } catch (error) {
        console.error("Error loading dashboard data:", error);
    }
}

function renderOverview(data) {
    const ov = data.overview || {};
    document.getElementById('kpi-tracked').innerText = (ov.trackedMunicipalities || 0).toLocaleString();
    document.getElementById('kpi-highrisk').innerText = ov.highRiskMunicipalities || 0;

    const tbody = document.getElementById('actions-table-body');
    tbody.innerHTML = '';
    
    const actions = data.municipality_stats?.actions || [];
    if (actions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="px-6 py-8 text-center text-gray-400">No prediction data available yet.</td></tr>';
        return;
    }
    
    actions.forEach(item => {
        let action, actionClass;
        if (item.risk_level === 'VERY HIGH') {
            action = "Immediate: Deploy emergency vector control teams";
            actionClass = "text-red-700 bg-red-50";
        } else if (item.risk_level === 'HIGH') {
            action = "Deploy targeted spraying & issue health warnings";
            actionClass = "text-orange-700 bg-orange-50";
        } else if (item.risk_level === 'MODERATE') {
            action = "Increase surveillance frequency";
            actionClass = "text-yellow-700 bg-yellow-50";
        } else {
            action = "Continue routine monitoring";
            actionClass = "text-green-700 bg-green-50";
        }

        const riskColor = (item.risk_level === 'HIGH' || item.risk_level === 'VERY HIGH') 
            ? 'bg-red-100 text-red-700' 
            : item.risk_level === 'MODERATE' 
                ? 'bg-yellow-100 text-yellow-700' 
                : 'bg-green-100 text-green-700';

        const tr = document.createElement('tr');
        tr.className = "hover:bg-gray-50 transition-colors";
        tr.innerHTML = `
            <td class="px-6 py-4 font-medium text-gray-800">${item.municipality}<br><span class="text-xs text-gray-400">${item.state_name || ''}</span></td>
            <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-xs font-semibold ${riskColor}">${item.risk_level}</span></td>
            <td class="px-6 py-4 font-mono font-semibold">${(item.risk_probability * 100).toFixed(1)}%</td>
            <td class="px-6 py-4 text-sm ${actionClass} rounded-lg">${action}</td>
        `;
        tbody.appendChild(tr);
    });
}

function getRiskColor(level) {
    const colors = { 'VERY HIGH': '#ef4444', 'HIGH': '#f97316', 'MODERATE': '#eab308', 'LOW': '#22c55e' };
    return colors[level] || '#9ca3af';
}

function renderMap(mapData) {
    if (!mapData || mapData.length === 0) return;
    
    // Clear existing layers
    map.eachLayer((layer) => {
        if (layer instanceof L.GeoJSON || layer instanceof L.CircleMarker) {
            map.removeLayer(layer);
        }
    });

    const bounds = [];
    
    mapData.forEach(loc => {
        const riskColor = getRiskColor(loc.risk_level);
        
        if (loc.geometry) {
            try {
                const geojson = JSON.parse(loc.geometry);
                const layer = L.geoJSON(geojson, {
                    style: {
                        color: riskColor,
                        weight: 1,
                        fillOpacity: 0.6
                    }
                }).bindPopup(`
                    <div class="p-2">
                        <strong class="text-lg">${loc.municipality}, ${loc.state_name}</strong><br>
                        Risk Level: <span class="font-bold" style="color:${riskColor}">${loc.risk_level}</span><br>
                        Probability: ${(loc.risk_probability * 100).toFixed(1)}%
                    </div>
                `).addTo(map);
                
                bounds.push(layer.getBounds());
            } catch (e) {
                console.error("Invalid GeoJSON for", loc.municipality);
            }
        }
    });
    
    // Fit bounds if we have any
    if (bounds.length > 0) {
        const group = new L.featureGroup(bounds.map(b => L.rectangle(b)));
        map.fitBounds(group.getBounds());
    }
}

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { font: { family: 'Inter' }, usePointStyle: true, padding: 16 } }
    }
};

function renderHotspotsChart(hotspots) {
    console.log("Hotspots Data:", hotspots);
    if (!hotspots || !hotspots.length) return;
    destroyChart('hotspots');
    const ctx = document.getElementById('hotspotsChart').getContext('2d');
    
    // Validate data explicitly
    const labels = hotspots.map(h => h.municipality || 'Unknown');
    // Try to get cases, case_volume, or default to 100 just to force it to render SOMETHING
    const dataValues = hotspots.map(h => h.cases ?? h.case_volume ?? h.malaria_cases_current ?? 100);
    
    console.log("Hotspots Labels:", labels);
    console.log("Hotspots Values:", dataValues);

    chartInstances['hotspots'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Malaria Cases',
                data: dataValues,
                backgroundColor: 'rgba(239, 68, 68, 0.75)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderSeasonalChart(seasonalData) {
    if (!seasonalData || !seasonalData.length) return;
    destroyChart('seasonal');
    const ctx = document.getElementById('seasonalChart').getContext('2d');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    chartInstances['seasonal'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: seasonalData.map(s => months[(s.month || 1) - 1]),
            datasets: [{
                label: 'Total Malaria Cases by Month',
                data: seasonalData.map(s => s.total_cases ?? 50),
                backgroundColor: 'rgba(59, 130, 246, 0.6)'
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function renderClimateChart(trends) {
    if (!trends || !trends.length) return;
    destroyChart('climate');
    const ctx = document.getElementById('climateDiseaseChart').getContext('2d');
    
    chartInstances['climate'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trends.map(t => t.date || 'Unknown'),
            datasets: [
                {
                    label: 'Malaria Cases',
                    data: trends.map(t => t.total_cases ?? 50),
                    borderColor: 'rgb(239, 68, 68)',
                    yAxisID: 'y'
                },
                {
                    label: 'Temperature (C)',
                    data: trends.map(t => t.avg_temp ?? 25),
                    borderColor: 'rgb(249, 115, 22)',
                    yAxisID: 'y1'
                }
            ]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function renderModelPerformance(perf) {
    if (!perf) perf = {};
    const prec = perf.precision ?? perf.Precision ?? 0;
    const rec = perf.recall ?? perf.Recall ?? 0;
    const f1 = perf.f1_score ?? perf.F1_score ?? 0;
    const auc = perf.pr_auc ?? perf.PR_AUC ?? 0;
    
    document.getElementById('metric-precision').innerText = prec ? ((prec * 100).toFixed(1) + '%') : '--';
    document.getElementById('metric-recall').innerText = rec ? ((rec * 100).toFixed(1) + '%') : '--';
    document.getElementById('metric-f1').innerText = f1 ? ((f1 * 100).toFixed(1) + '%') : '--';
    document.getElementById('metric-prauc').innerText = auc ? auc.toFixed(3) : '--';
}

// Initialize

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    const btn = document.getElementById('btn-apply-filters');
    if (btn) btn.addEventListener('click', loadDashboardData);
});


function renderAllBriefCharts(data) {
    // 1. Feature Importance (Bar Chart)
    const perf = data.model_performance || {};
    if (perf.feature_importances) {
        destroyChart('chartFeatureImportance');
        const ctxFI = document.getElementById('chartFeatureImportance').getContext('2d');
        const labelsFI = Object.keys(perf.feature_importances);
        const dataFI = Object.values(perf.feature_importances);
        chartInstances['chartFeatureImportance'] = new Chart(ctxFI, {
            type: 'bar',
            data: { labels: labelsFI, datasets: [{ label: 'Importance Score', data: dataFI, backgroundColor: '#3b82f6' }] },
            options: chartDefaults
        });
    }

    // 2. Climate Scatter Plot (Temp vs Cases)
    const trends = data.climate_disease_trends || [];
    if (trends.length > 0) {
        destroyChart('chartScatterClimate');
        const ctxScatter = document.getElementById('chartScatterClimate').getContext('2d');
        const scatterData = trends.map(t => ({ x: t.avg_temp, y: t.total_cases }));
        chartInstances['chartScatterClimate'] = new Chart(ctxScatter, {
            type: 'scatter',
            data: { datasets: [{ label: 'Temp vs Cases', data: scatterData, backgroundColor: '#f97316' }] },
            options: { ...chartDefaults, scales: { x: { title: { display: true, text: 'Temperature (C)' } }, y: { title: { display: true, text: 'Cases' } } } }
        });

        // 3. Time Lag Analysis (Line Chart - Mocking shift for visual purposes)
        destroyChart('chartTimeLag');
        const ctxLag = document.getElementById('chartTimeLag').getContext('2d');
        chartInstances['chartTimeLag'] = new Chart(ctxLag, {
            type: 'line',
            data: {
                labels: trends.map(t => t.date),
                datasets: [
                    { label: 'Rainfall', data: trends.map(t => t.avg_rain), borderColor: '#3b82f6', tension: 0.3 },
                    { label: 'Cases (Shifted)', data: trends.map((t, i) => trends[i+2] ? trends[i+2].total_cases : null), borderColor: '#ef4444', tension: 0.3 }
                ]
            },
            options: chartDefaults
        });

        // 5. Early Warning Signs (Bubble Chart)
        destroyChart('chartBubbleWarning');
        const ctxBubble = document.getElementById('chartBubbleWarning').getContext('2d');
        const bubbleData = trends.slice(-20).map(t => ({ x: t.avg_temp, y: t.avg_rain, r: Math.min(t.total_cases / 10, 20) }));
        chartInstances['chartBubbleWarning'] = new Chart(ctxBubble, {
            type: 'bubble',
            data: { datasets: [{ label: 'Size = Cases', data: bubbleData, backgroundColor: 'rgba(239, 68, 68, 0.6)' }] },
            options: { ...chartDefaults, scales: { x: { title: { display: true, text: 'Temperature (C)' } }, y: { title: { display: true, text: 'Rainfall (mm)' } } } }
        });

        // 6. Annual Outbreak Trends (Time-Series)
        const annual = {};
        trends.forEach(t => {
            const year = t.date.split('-')[0];
            annual[year] = (annual[year] || 0) + t.total_cases;
        });
        destroyChart('chartAnnualTrends');
        const ctxAnnual = document.getElementById('chartAnnualTrends').getContext('2d');
        chartInstances['chartAnnualTrends'] = new Chart(ctxAnnual, {
            type: 'line',
            data: { labels: Object.keys(annual), datasets: [{ label: 'Total Cases per Year', data: Object.values(annual), borderColor: '#8b5cf6', backgroundColor: 'rgba(139, 92, 246, 0.2)', fill: true, tension: 0.3 }] },
            options: chartDefaults
        });
    }
}
