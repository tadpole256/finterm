"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  type CandlestickData,
  ColorType,
  createChart,
  type HistogramData,
  type ISeriesApi,
  type LineData,
  LineStyle,
  type UTCTimestamp
} from "lightweight-charts";

import type { SecurityWorkspacePayload } from "@/lib/types";

interface SecurityChartProps {
  data: SecurityWorkspacePayload;
  showSma20: boolean;
  showSma50: boolean;
  showEma20: boolean;
  showRsi: boolean;
  showMacd: boolean;
}

function toTimestamp(value: string): UTCTimestamp {
  return Math.floor(new Date(value).getTime() / 1000) as UTCTimestamp;
}

export function SecurityChart({
  data,
  showSma20,
  showSma50,
  showEma20,
  showRsi,
  showMacd
}: SecurityChartProps) {
  const mainContainerRef = useRef<HTMLDivElement | null>(null);
  const rsiContainerRef = useRef<HTMLDivElement | null>(null);
  const macdContainerRef = useRef<HTMLDivElement | null>(null);

  const candleData = useMemo<CandlestickData[]>(
    () =>
      data.bars.map((bar) => ({
        time: toTimestamp(bar.ts),
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close
      })),
    [data.bars]
  );

  useEffect(() => {
    const mainElement = mainContainerRef.current;
    if (!mainElement) {
      return;
    }

    mainElement.innerHTML = "";

    const mainChart = createChart(mainElement, {
      width: mainElement.clientWidth,
      height: 420,
      layout: {
        background: { type: ColorType.Solid, color: "#111827" },
        textColor: "#dbe7ff"
      },
      grid: {
        vertLines: { color: "#1f2b43" },
        horzLines: { color: "#1f2b43" }
      },
      rightPriceScale: {
        borderColor: "#2c3c58"
      },
      timeScale: {
        borderColor: "#2c3c58"
      }
    });

    const candleSeries = mainChart.addCandlestickSeries({
      upColor: "#2ecc71",
      downColor: "#ff6b6b",
      borderVisible: false,
      wickUpColor: "#2ecc71",
      wickDownColor: "#ff6b6b"
    });
    candleSeries.setData(candleData);

    const volumeSeries = mainChart.addHistogramSeries({
      priceFormat: {
        type: "volume"
      },
      priceScaleId: "",
      color: "#355d8a",
      base: 0
    });

    const volumeData: HistogramData[] = data.bars.map((bar) => ({
      time: toTimestamp(bar.ts),
      value: bar.volume,
      color: bar.close >= bar.open ? "#2ecc7155" : "#ff6b6b55"
    }));
    volumeSeries.setData(volumeData);

    const indicatorSeries: ISeriesApi<"Line">[] = [];

    if (showSma20) {
      const series = mainChart.addLineSeries({ color: "#f6c343", lineWidth: 2 });
      series.setData(
        data.indicators.sma20
          .filter((point) => point.value !== null)
          .map((point) => ({ time: toTimestamp(point.ts), value: point.value as number }))
      );
      indicatorSeries.push(series);
    }

    if (showSma50) {
      const series = mainChart.addLineSeries({ color: "#7ad1ff", lineWidth: 2, lineStyle: LineStyle.Dotted });
      series.setData(
        data.indicators.sma50
          .filter((point) => point.value !== null)
          .map((point) => ({ time: toTimestamp(point.ts), value: point.value as number }))
      );
      indicatorSeries.push(series);
    }

    if (showEma20) {
      const series = mainChart.addLineSeries({ color: "#ff9f43", lineWidth: 2 });
      series.setData(
        data.indicators.ema20
          .filter((point) => point.value !== null)
          .map((point) => ({ time: toTimestamp(point.ts), value: point.value as number }))
      );
      indicatorSeries.push(series);
    }

    const onResize = () => {
      mainChart.applyOptions({ width: mainElement.clientWidth });
    };

    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      indicatorSeries.forEach((series) => mainChart.removeSeries(series));
      mainChart.remove();
    };
  }, [candleData, data.bars, data.indicators, showSma20, showSma50, showEma20]);

  useEffect(() => {
    const rsiElement = rsiContainerRef.current;
    if (!showRsi || !rsiElement) {
      return;
    }

    rsiElement.innerHTML = "";

    const rsiChart = createChart(rsiElement, {
      width: rsiElement.clientWidth,
      height: 160,
      layout: {
        background: { type: ColorType.Solid, color: "#111827" },
        textColor: "#dbe7ff"
      },
      grid: {
        vertLines: { color: "#1f2b43" },
        horzLines: { color: "#1f2b43" }
      }
    });

    const series = rsiChart.addLineSeries({ color: "#9b59b6", lineWidth: 2 });
    const points: LineData[] = data.indicators.rsi14
      .filter((point) => point.value !== null)
      .map((point) => ({ time: toTimestamp(point.ts), value: point.value as number }));
    series.setData(points);

    const onResize = () => {
      rsiChart.applyOptions({ width: rsiElement.clientWidth });
    };

    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      rsiChart.remove();
    };
  }, [data.indicators.rsi14, showRsi]);

  useEffect(() => {
    const macdElement = macdContainerRef.current;
    if (!showMacd || !macdElement) {
      return;
    }

    macdElement.innerHTML = "";

    const macdChart = createChart(macdElement, {
      width: macdElement.clientWidth,
      height: 180,
      layout: {
        background: { type: ColorType.Solid, color: "#111827" },
        textColor: "#dbe7ff"
      },
      grid: {
        vertLines: { color: "#1f2b43" },
        horzLines: { color: "#1f2b43" }
      }
    });

    const macdSeries = macdChart.addLineSeries({ color: "#00d2d3", lineWidth: 2 });
    const signalSeries = macdChart.addLineSeries({ color: "#ff9f43", lineWidth: 2 });
    const histogram = macdChart.addHistogramSeries({
      color: "#3aa3ff",
      priceFormat: { type: "price", precision: 4, minMove: 0.0001 }
    });

    macdSeries.setData(
      data.indicators.macd
        .filter((point) => point.macd !== null)
        .map((point) => ({ time: toTimestamp(point.ts), value: point.macd as number }))
    );

    signalSeries.setData(
      data.indicators.macd
        .filter((point) => point.signal !== null)
        .map((point) => ({ time: toTimestamp(point.ts), value: point.signal as number }))
    );

    histogram.setData(
      data.indicators.macd
        .filter((point) => point.histogram !== null)
        .map((point) => ({
          time: toTimestamp(point.ts),
          value: point.histogram as number,
          color: (point.histogram as number) >= 0 ? "#2ecc7155" : "#ff6b6b55"
        }))
    );

    const onResize = () => {
      macdChart.applyOptions({ width: macdElement.clientWidth });
    };

    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      macdChart.remove();
    };
  }, [data.indicators.macd, showMacd]);

  return (
    <div className="space-y-3">
      <div ref={mainContainerRef} className="w-full overflow-hidden rounded-lg border border-border" />
      {showRsi ? <div ref={rsiContainerRef} className="w-full rounded-lg border border-border" /> : null}
      {showMacd ? <div ref={macdContainerRef} className="w-full rounded-lg border border-border" /> : null}
    </div>
  );
}
