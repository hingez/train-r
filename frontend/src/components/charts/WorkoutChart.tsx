import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from "recharts";
import type { WorkoutData } from "@/types/workout";
import { getPowerPercent, TRAINING_ZONES, getTrainingZoneColor, getTrainingZoneDefinition } from "@/types/workout";

interface WorkoutChartProps {
  workoutData: WorkoutData;
  showFTPLine?: boolean;
  showZoneOverlays?: boolean;
}

export function WorkoutChart({ workoutData, showFTPLine = true, showZoneOverlays = true }: WorkoutChartProps) {
  const { segments, ftp } = workoutData;
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const powerPercent = getPowerPercent(data.power, ftp);
      const zoneDef = data.trainingZone ? getTrainingZoneDefinition(data.trainingZone) : null;

      return (
        <div className="bg-card border-none rounded-lg shadow-xl p-3 text-sm min-w-[180px] bg-slate-900/90 text-white backdrop-blur-sm">
          {data.label && <p className="font-bold text-base mb-1.5 text-white/90">{data.label}</p>}
          <div className="space-y-1">
            <p className="text-gray-300 text-xs">
              <span className="font-medium text-gray-400">Time:</span> {data.time}
            </p>
            <p className="font-bold text-primary-foreground text-sm">
              {data.power}W <span className="text-gray-400 font-normal">({powerPercent}% FTP)</span>
            </p>
            {zoneDef && (
              <div className="mt-2 pt-2 border-t border-white/10">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: zoneDef.color }}
                  />
                  <span className="font-semibold text-xs">{zoneDef.zone} - {zoneDef.name}</span>
                </div>
                <p className="text-[10px] text-gray-400 mt-0.5">{zoneDef.description}</p>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  // Format Y-axis labels (power)
  const formatPower = (value: number) => `${value}W`;

  // Dynamic label interval based on workout duration and segment count
  const totalSegments = segments.length;
  const { totalDuration } = workoutData;

  // Calculate optimal label interval to show roughly 10-15 labels
  let targetLabels = 12;
  if (totalDuration < 1800) {
    // Short workouts (<30min): show more labels
    targetLabels = 15;
  } else if (totalDuration > 5400) {
    // Long workouts (>90min): show fewer labels
    targetLabels = 10;
  }
  const labelInterval = Math.ceil(totalSegments / targetLabels);

  // Calculate max power for chart domain
  const maxPower = Math.max(...segments.map(s => s.power));
  const chartMax = Math.ceil(maxPower * 1.1 / 50) * 50; // Round up to nearest 50W

  return (
    <section className="bg-card-light dark:bg-card-dark rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col">
      <div className="p-4 border-b border-gray-100 dark:border-gray-700">
        <h2 className="font-semibold text-base">Workout Profile</h2>
      </div>

      <div className="p-4 flex flex-col">
        <div className="relative h-[360px] w-full bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-dashed border-gray-300 dark:border-gray-600 flex items-center justify-center overflow-hidden">
          <div className="w-full h-full absolute inset-0 pt-3 pr-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={segments}
                margin={{ top: 10, right: 10, left: 0, bottom: 40 }}
                onMouseMove={(state: any) => {
                  if (state.isTooltipActive) {
                    setHoveredIndex(state.activeTooltipIndex);
                  } else {
                    setHoveredIndex(null);
                  }
                }}
                onMouseLeave={() => setHoveredIndex(null)}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} vertical={false} />

                {/* Zone overlay backgrounds */}
                {showZoneOverlays && TRAINING_ZONES.map((zone) => {
                  const y1 = (zone.minPercent / 100) * ftp;
                  const y2 = Math.min((zone.maxPercent / 100) * ftp, chartMax);

                  return (
                    <ReferenceArea
                      key={zone.zone}
                      y1={y1}
                      y2={y2}
                      fill={zone.color}
                      fillOpacity={0.05}
                      stroke="none"
                    />
                  );
                })}

                <XAxis
                  dataKey="time"
                  stroke="#9CA3AF"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  interval={labelInterval}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                  tickMargin={10}
                  style={{ fontWeight: 500 }}
                />

                <YAxis
                  stroke="#9CA3AF"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={formatPower}
                  domain={[0, chartMax]}
                  style={{ fontWeight: 500 }}
                />

                <Tooltip
                  content={<CustomTooltip />}
                  cursor={{ fill: 'hsl(var(--primary))', opacity: 0.05 }}
                />

                {/* FTP Reference Line */}
                {showFTPLine && (
                  <ReferenceLine
                    y={ftp}
                    stroke="hsl(var(--primary))"
                    strokeDasharray="5 5"
                    strokeWidth={1.5}
                    label={{
                      value: "FTP",
                      position: 'insideTopRight',
                      fill: 'hsl(var(--primary))',
                      fontSize: 10,
                      fontWeight: 'bold',
                      offset: 10
                    }}
                  />
                )}

                {/* Bar with dynamic colors and hover effects */}
                <Bar
                  dataKey="power"
                  fill="hsl(var(--primary))"
                  radius={[4, 4, 0, 0]}
                  shape={(props: any) => {
                    const { x, y, width, height, payload, index } = props;
                    const isHovered = index === hoveredIndex;
                    const fillColor = payload.trainingZone
                      ? getTrainingZoneColor(payload.trainingZone)
                      : 'hsl(var(--muted))';

                    return (
                      <g>
                        <rect
                          x={x}
                          y={y}
                          width={width}
                          height={height}
                          fill={fillColor}
                          opacity={isHovered ? 1 : 0.85}
                          rx={Math.min(4, width / 2)}
                          ry={Math.min(4, width / 2)}
                          style={{
                            transition: 'all 0.2s ease',
                            filter: isHovered ? 'brightness(1.1)' : 'none',
                          }}
                        />
                      </g>
                    );
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Training Zones Legend */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
          {TRAINING_ZONES.map((zone) => (
            <div
              key={zone.zone}
              className="bg-gray-50 dark:bg-gray-800 rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-default border border-transparent hover:border-gray-200 dark:hover:border-gray-600"
            >
              <div className="flex items-center gap-2 mb-1">
                <div
                  className="w-2 h-2 rounded-full shadow-sm"
                  style={{ backgroundColor: zone.color }}
                />
                <p className="text-[10px] text-subtext-light dark:text-subtext-dark uppercase font-bold tracking-wider">
                  {zone.zone}
                </p>
              </div>

              <div className="space-y-0.5">
                <p className="text-xs font-bold text-foreground truncate" title={zone.name}>
                  {zone.name}
                </p>
                <p className="text-xs font-semibold text-muted-foreground">
                  {zone.minPercent}-{zone.maxPercent}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
