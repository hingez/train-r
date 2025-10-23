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
        <div className="bg-card border-2 border-primary rounded-lg shadow-xl p-4 text-sm min-w-[200px]">
          {data.label && <p className="font-bold text-lg mb-2">{data.label}</p>}
          <div className="space-y-1">
            <p className="text-muted-foreground">
              <span className="font-medium">Time:</span> {data.time}
            </p>
            <p className="font-semibold text-primary text-base">
              {data.power}W <span className="text-muted-foreground">({powerPercent}% FTP)</span>
            </p>
            {zoneDef && (
              <div className="mt-2 pt-2 border-t border-border">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: zoneDef.color }}
                  />
                  <span className="font-semibold">{zoneDef.zone} - {zoneDef.name}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">{zoneDef.description}</p>
                <p className="text-xs text-muted-foreground">
                  {zoneDef.minPercent}-{zoneDef.maxPercent}% FTP
                </p>
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

  // Sample every Nth segment for X-axis labels to avoid crowding
  const totalSegments = segments.length;
  const labelInterval = Math.ceil(totalSegments / 12);

  // Calculate max power for chart domain
  const maxPower = Math.max(...segments.map(s => s.power));
  const chartMax = Math.ceil(maxPower * 1.1 / 50) * 50; // Round up to nearest 50W

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={450}>
        <BarChart
          data={segments}
          margin={{ top: 30, right: 30, left: 20, bottom: 60 }}
          onMouseMove={(state: any) => {
            if (state.isTooltipActive) {
              setHoveredIndex(state.activeTooltipIndex);
            } else {
              setHoveredIndex(null);
            }
          }}
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />

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
                fillOpacity={0.08}
                stroke="none"
              />
            );
          })}

          <XAxis
            dataKey="time"
            stroke="hsl(var(--foreground))"
            fontSize={12}
            tickLine={false}
            interval={labelInterval}
            angle={-45}
            textAnchor="end"
            height={60}
          />

          <YAxis
            stroke="hsl(var(--foreground))"
            fontSize={12}
            tickLine={false}
            tickFormatter={formatPower}
            domain={[0, chartMax]}
          />

          <Tooltip
            content={<CustomTooltip />}
            cursor={{ fill: 'hsl(var(--primary))', opacity: 0.1 }}
          />

          {/* FTP Reference Line */}
          {showFTPLine && (
            <ReferenceLine
              y={ftp}
              stroke="hsl(var(--primary))"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: `FTP: ${ftp}W (100%)`,
                position: 'right',
                fill: 'hsl(var(--primary))',
                fontSize: 12,
                fontWeight: 'bold',
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
                    rx={4}
                    ry={4}
                    style={{
                      transition: 'all 0.2s ease',
                      filter: isHovered ? 'brightness(1.2)' : 'none',
                      stroke: isHovered ? fillColor : 'none',
                      strokeWidth: isHovered ? 2 : 0,
                    }}
                  />
                  {isHovered && (
                    <rect
                      x={x}
                      y={y}
                      width={width}
                      height={height}
                      fill="white"
                      opacity={0.2}
                      rx={4}
                      ry={4}
                      pointerEvents="none"
                    />
                  )}
                </g>
              );
            }}
          />
        </BarChart>
      </ResponsiveContainer>

      {/* Training Zones Legend */}
      <div className="mt-6 border-t border-border pt-4">
        <h4 className="text-sm font-semibold mb-3 text-center">Training Zones (% of FTP)</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 text-xs">
          {TRAINING_ZONES.map((zone) => (
            <div
              key={zone.zone}
              className="flex flex-col items-center p-2 rounded-md border border-border hover:bg-accent transition-colors"
            >
              <div
                className="w-8 h-8 rounded-full mb-1 border-2 border-white shadow-sm"
                style={{ backgroundColor: zone.color }}
              />
              <span className="font-bold">{zone.zone}</span>
              <span className="text-muted-foreground text-center leading-tight">{zone.name}</span>
              <span className="text-muted-foreground">{zone.minPercent}-{zone.maxPercent}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
