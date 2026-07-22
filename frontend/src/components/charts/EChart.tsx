import type { ComponentProps } from "react";
import ReactEChartsCore from "echarts-for-react/esm/core";
import * as echarts from "echarts/core";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  CanvasRenderer,
]);

type EChartProps = Omit<ComponentProps<typeof ReactEChartsCore>, "echarts">;

export default function EChart(props: EChartProps) {
  return <ReactEChartsCore echarts={echarts} {...props} />;
}
