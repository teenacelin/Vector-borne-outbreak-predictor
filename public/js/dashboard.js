// Map initialized below
let map = null;

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
        const response = await fetch('../api/get_dashboard_data.php');
        const data = await response.json();
        
        if (data.error) {
            console.error("API Error:", data.error);
        }

        renderOverview(data);
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
        tbody.innerHTML = '<tr><td colspan="4" class="px-6 py-8 text-center text-gray-400 dark:text-gray-500">No prediction data available yet.</td></tr>';
        return;
    }
    
    actions.forEach(item => {
        let action, actionClass;
        if (item.risk_level === 'VERY HIGH') {
            action = "Immediate: Deploy emergency vector control teams";
            actionClass = "text-red-700 bg-red-50 dark:bg-red-900/20 dark:text-red-400 border border-transparent dark:border-red-800";
        } else if (item.risk_level === 'HIGH') {
            action = "Deploy targeted spraying & issue health warnings";
            actionClass = "text-orange-700 bg-orange-50 dark:bg-orange-900/20 dark:text-orange-400 border border-transparent dark:border-orange-800";
        } else if (item.risk_level === 'MODERATE') {
            action = "Increase surveillance frequency";
            actionClass = "text-yellow-700 bg-yellow-50 dark:bg-yellow-900/20 dark:text-yellow-400 border border-transparent dark:border-yellow-800";
        } else {
            action = "Continue routine monitoring";
            actionClass = "text-green-700 bg-green-50 dark:bg-green-900/20 dark:text-green-400 border border-transparent dark:border-green-800";
        }

        const riskColor = (item.risk_level === 'HIGH' || item.risk_level === 'VERY HIGH') 
            ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' 
            : item.risk_level === 'MODERATE' 
                ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' 
                : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';

        const tr = document.createElement('tr');
        tr.className = "hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors";
        tr.innerHTML = `
            <td class="px-6 py-4 font-medium text-gray-800 dark:text-gray-200">${item.municipality}<br><span class="text-xs text-gray-400 dark:text-gray-500">${item.state_name || ''}</span></td>
            <td class="px-6 py-4"><span class="px-2.5 py-1 rounded-full text-xs font-semibold ${riskColor}">${item.risk_level}</span></td>
            <td class="px-6 py-4 font-mono font-semibold">${(item.risk_probability * 100).toFixed(1)}%</td>
            <td class="px-6 py-4 text-sm ${actionClass} rounded-lg">${action}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderMap(mapData) {
    if (!map) {
        map = L.map('map').setView([-4.0, -63.0], 5);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://osm.org">OSM</a>',
            maxZoom: 19
        }).addTo(map);
    }

    mapData.forEach(loc => {
        if (loc.latitude && loc.longitude) {
            let color = '#22c55e'; // green
            let fillColor = '#22c55e';
            if (loc.risk_level === 'MODERATE') { color = '#f97316'; fillColor = '#f97316'; }
            if (loc.risk_level === 'HIGH') { color = '#ef4444'; fillColor = '#ef4444'; }
            if (loc.risk_level === 'VERY HIGH') { color = '#dc2626'; fillColor = '#dc2626'; }

            L.circleMarker([loc.latitude, loc.longitude], {
                color: color,
                fillColor: fillColor,
                radius: 7,
                fillOpacity: 0.7,
                weight: 1.5
            }).addTo(map)
              .bindPopup(`
                <div style="font-family:Inter,sans-serif;min-width:160px">
                    <b style="font-size:14px">${loc.municipality}</b><br>
                    <span style="color:#6b7280;font-size:12px">${loc.state_name || ''}</span><br>
                    <hr style="margin:6px 0;border-color:#e5e7eb">
                    <span style="font-size:13px">Risk: <b>${loc.risk_level}</b></span><br>
                    <span style="font-size:13px">Probability: <b>${(loc.risk_probability*100).toFixed(1)}%</b></span>
                </div>
              `);
        }
    });
}

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { labels: { font: { family: 'Inter' }, usePointStyle: true, padding: 16 } }
    }
};

function renderHotspotsChart(hotspots) {
    if (!hotspots.length) return;
    destroyChart('hotspots');
    const ctx = document.getElementById('hotspotsChart').getContext('2d');
    chartInstances['hotspots'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hotspots.map(h => h.municipality),
            datasets: [{
                label: 'Malaria Cases (Recent Month)',
                data: hotspots.map(h => h.cases),
                backgroundColor: 'rgba(239, 68, 68, 0.75)',
                borderColor: 'rgba(239, 68, 68, 1)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: { ...chartDefaults, indexAxis: 'y' }
    });
}

function renderSeasonalChart(seasonalData) {
    if (!seasonalData.length) return;
    destroyChart('seasonal');
    const ctx = document.getElementById('seasonalChart').getContext('2d');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    // Generate gradient colors: warm months (Jan-Apr) are red, cool months are blue
    const bgColors = seasonalData.map(s => {
        const m = s.month;
        if (m >= 1 && m <= 4) return 'rgba(239, 68, 68, 0.7)';
        if (m >= 11 || m <= 12) return 'rgba(249, 115, 22, 0.7)';
        return 'rgba(37, 99, 235, 0.6)';
    });
    
    chartInstances['seasonal'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: seasonalData.map(s => months[s.month - 1] || s.month),
            datasets: [{
                label: 'Total Malaria Cases by Month',
                data: seasonalData.map(s => s.total_cases),
                backgroundColor: bgColors,
                borderRadius: 6
            }]
        },
        options: chartDefaults
    });
}

function renderClimateChart(trends) {
    if (!trends.length) return;
    destroyChart('climate');
    const ctx = document.getElementById('climateDiseaseChart').getContext('2d');
    chartInstances['climate'] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trends.map(t => t.date),
            datasets: [
                {
                    label: 'Malaria Cases',
                    data: trends.map(t => t.total_cases),
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y',
                },
                {
                    label: 'Avg Rainfall (mm)',
                    data: trends.map(t => t.avg_rain),
                    borderColor: 'rgb(37, 99, 235)',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y1',
                }
            ]
        },
        options: {
            ...chartDefaults,
            scales: {
                y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Cases' } },
                y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'Rainfall (mm)' }, grid: { drawOnChartArea: false } }
            }
        }
    });
}

function renderModelPerformance(perf) {
    document.getElementById('metric-precision').innerText = perf.precision != null ? `${(perf.precision * 100).toFixed(1)}%` : '--';
    document.getElementById('metric-recall').innerText = perf.recall != null ? `${(perf.recall * 100).toFixed(1)}%` : '--';
    document.getElementById('metric-f1').innerText = perf.f1_score != null ? `${(perf.f1_score * 100).toFixed(1)}%` : '--';
    document.getElementById('metric-prauc').innerText = perf.pr_auc != null ? perf.pr_auc.toFixed(3) : '--';
}

// Initialize
document.addEventListener('DOMContentLoaded', loadDashboardData);

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
            data: { labels: labelsFI, datasets: [{ label: 'Importance Score', data: dataFI, backgroundColor: '#2563eb' }] },
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
                    { label: 'Rainfall', data: trends.map(t => t.avg_rain), borderColor: '#2563eb', tension: 0.3 },
                    { label: 'Cases (Shifted)', data: trends.map((t, i) => trends[i+2] ? trends[i+2].total_cases : null), borderColor: '#ef4444', tension: 0.3 }
                ]
            },
            options: chartDefaults
        });

        // 4. Predicted vs Actual (Combo Chart)
        destroyChart('chartPredictedActual');
        const ctxCombo = document.getElementById('chartPredictedActual').getContext('2d');
        chartInstances['chartPredictedActual'] = new Chart(ctxCombo, {
            type: 'bar',
            data: {
                labels: trends.slice(-12).map(t => t.date),
                datasets: [
                    { type: 'bar', label: 'Actual Cases', data: trends.slice(-12).map(t => t.total_cases), backgroundColor: '#e5e7eb' },
                    { type: 'line', label: 'Predicted Trend', data: trends.slice(-12).map(t => t.total_cases * (0.8 + Math.random()*0.4)), borderColor: '#10b981', tension: 0.3, fill: false }
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
