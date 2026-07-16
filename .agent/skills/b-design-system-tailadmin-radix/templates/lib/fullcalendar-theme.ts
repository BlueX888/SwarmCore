import { deepMergeOptions } from "./merge-options";

/** TailAdmin event level → semantic palette (align token-index) */
export const eventLevelPalette = {
  Primary: { bg: "brand", dot: "brand-500", bgClass: "fc-bg-primary" },
  Success: { bg: "success", dot: "success-500", bgClass: "fc-bg-success" },
  Danger: { bg: "error", dot: "error-500", bgClass: "fc-bg-danger" },
  Warning: { bg: "orange", dot: "orange-500", bgClass: "fc-bg-warning" },
} as const;

export type EventLevel = keyof typeof eventLevelPalette;

export const eventLevelClassMap: Record<EventLevel, string> = {
  Primary: eventLevelPalette.Primary.bgClass,
  Success: eventLevelPalette.Success.bgClass,
  Danger: eventLevelPalette.Danger.bgClass,
  Warning: eventLevelPalette.Warning.bgClass,
};

export const defaultHeaderToolbar = {
  left: "prev,next addEventButton",
  center: "title",
  right: "dayGridMonth,timeGridWeek,timeGridDay",
} as const;

export const defaultCustomButtons = {
  addEventButton: {
    text: "Add Event +",
  },
} as const;

export type FullCalendarDefaultOptions = {
  initialView: "dayGridMonth";
  headerToolbar: typeof defaultHeaderToolbar;
  customButtons: typeof defaultCustomButtons;
  selectable: boolean;
  editable: boolean;
  dayMaxEvents: boolean;
};

const baseFullCalendarOptions = {
  initialView: "dayGridMonth" as const,
  headerToolbar: defaultHeaderToolbar,
  customButtons: defaultCustomButtons,
  selectable: true,
  editable: false,
  dayMaxEvents: true,
};

export function getDefaultFullCalendarOptions(
  overrides?: Partial<FullCalendarDefaultOptions> & Record<string, unknown>
): FullCalendarDefaultOptions & Record<string, unknown> {
  return deepMergeOptions(baseFullCalendarOptions, overrides) as FullCalendarDefaultOptions &
    Record<string, unknown>;
}

/** Match source Calendar.tsx renderEventContent className */
export function getEventContentClassName(level: EventLevel | string): string {
  const colorClass =
    eventLevelClassMap[level as EventLevel] ?? eventLevelPalette.Primary.bgClass;
  return `event-fc-color flex fc-event-main ${colorClass} p-1 rounded-sm`;
}

/** Copy into host src/index.css — requires Tailwind v4 @apply */
export const fullCalendarCssOverrides = `
.fc .fc-view-harness {
  @apply max-w-full overflow-x-auto custom-scrollbar;
}
.fc-dayGridMonth-view.fc-view.fc-daygrid {
  @apply min-w-[718px];
}
.fc .fc-scrollgrid-section > * {
  border-right-width: 0;
  border-bottom-width: 0;
}
.fc .fc-scrollgrid {
  border-left-width: 0;
}
.fc .fc-toolbar.fc-header-toolbar {
  @apply flex-col gap-4 px-6 pt-6 sm:flex-row;
}
.fc-button-group {
  @apply gap-2;
}
.fc-button-group .fc-button {
  @apply flex h-10 w-10 items-center justify-center !rounded-lg border border-gray-200 bg-transparent hover:border-gray-200 hover:bg-gray-50 focus:shadow-none active:!border-gray-200 active:!bg-transparent active:!shadow-none dark:border-gray-800 dark:hover:border-gray-800 dark:hover:bg-gray-900 dark:active:!border-gray-800;
}
.fc-button-group .fc-button.fc-prev-button:before {
  @apply inline-block mt-1;
  content: url("data:image/svg+xml,%3Csvg width='25' height='24' viewBox='0 0 25 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M16.0068 6L9.75684 12.25L16.0068 18.5' stroke='%23344054' strokeWidth='1.5' strokeLinecap='round' strokeLinejoin='round'/%3E%3C/svg%3E%0A");
}
.fc-button-group .fc-button.fc-next-button:before {
  @apply inline-block mt-1;
  content: url("data:image/svg+xml,%3Csvg width='25' height='24' viewBox='0 0 25 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M9.50684 19L15.7568 12.75L9.50684 6.5' stroke='%23344054' strokeWidth='1.5' strokeLinecap='round' strokeLinejoin='round'/%3E%3C/svg%3E%0A");
}
.dark .fc-button-group .fc-button.fc-prev-button:before {
  content: url("data:image/svg+xml,%3Csvg width='25' height='24' viewBox='0 0 25 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M16.0068 6L9.75684 12.25L16.0068 18.5' stroke='%2398A2B3' strokeWidth='1.5' strokeLinecap='round' strokeLinejoin='round'/%3E%3C/svg%3E%0A");
}
.dark .fc-button-group .fc-button.fc-next-button:before {
  content: url("data:image/svg+xml,%3Csvg width='25' height='24' viewBox='0 0 25 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M9.50684 19L15.7568 12.75L9.50684 6.5' stroke='%2398A2B3' strokeWidth='1.5' strokeLinecap='round' strokeLinejoin='round'/%3E%3C/svg%3E%0A");
}
.fc-button-group .fc-button .fc-icon {
  @apply hidden;
}
.fc-addEventButton-button {
  @apply !rounded-lg !border-0 !bg-brand-500 !px-4 !py-2.5 !text-sm !font-medium hover:!bg-brand-600 focus:!shadow-none;
}
.fc-toolbar-title {
  @apply !text-lg !font-medium text-gray-800 dark:text-white/90;
}
.fc-header-toolbar.fc-toolbar .fc-toolbar-chunk:last-child {
  @apply rounded-lg bg-gray-100 p-0.5 dark:bg-gray-900;
}
.fc-header-toolbar.fc-toolbar .fc-toolbar-chunk:last-child .fc-button {
  @apply !h-auto !w-auto rounded-md !border-0 bg-transparent !px-5 !py-2 text-sm font-medium text-gray-500 hover:text-gray-700 focus:!shadow-none dark:text-gray-400;
}
.fc-header-toolbar.fc-toolbar .fc-toolbar-chunk:last-child .fc-button.fc-button-active {
  @apply text-gray-900 bg-white dark:bg-gray-800 dark:text-white;
}
.fc-theme-standard th {
  @apply !border-x-0 border-t !border-gray-200 bg-gray-50 !text-left dark:!border-gray-800 dark:bg-gray-900;
}
.fc-theme-standard td,
.fc-theme-standard .fc-scrollgrid {
  @apply !border-gray-200 dark:!border-gray-800;
}
.fc .fc-col-header-cell-cushion {
  @apply !px-5 !py-4 text-sm font-medium uppercase text-gray-400;
}
.fc .fc-daygrid-day.fc-day-today {
  @apply bg-transparent;
}
.fc .fc-daygrid-day {
  @apply p-2;
}
.fc .fc-daygrid-day.fc-day-today .fc-scrollgrid-sync-inner {
  @apply rounded-sm bg-gray-100 dark:bg-white/[0.03];
}
.fc .fc-daygrid-day-number {
  @apply !p-3 text-sm font-medium text-gray-700 dark:text-gray-400;
}
.fc .fc-daygrid-day-top {
  @apply !flex-row;
}
.fc .fc-day-other .fc-daygrid-day-top {
  opacity: 1;
}
.fc .fc-day-other .fc-daygrid-day-top .fc-daygrid-day-number {
  @apply text-gray-400 dark:text-white/30;
}
.event-fc-color {
  @apply rounded-lg py-2.5 pl-4 pr-3;
}
.event-fc-color .fc-event-title {
  @apply p-0 text-sm font-normal text-gray-700;
}
.fc-daygrid-event-dot {
  @apply w-1 h-5 ml-0 mr-3 border-none rounded-sm;
}
.fc-event {
  @apply focus:shadow-none;
}
.fc-daygrid-event.fc-event-start {
  @apply !ml-3;
}
.event-fc-color.fc-bg-success {
  @apply border-success-50 bg-success-50;
}
.event-fc-color.fc-bg-danger {
  @apply border-error-50 bg-error-50;
}
.event-fc-color.fc-bg-primary {
  @apply border-brand-50 bg-brand-50;
}
.event-fc-color.fc-bg-warning {
  @apply border-orange-50 bg-orange-50;
}
.event-fc-color.fc-bg-success .fc-daygrid-event-dot {
  @apply bg-success-500;
}
.event-fc-color.fc-bg-danger .fc-daygrid-event-dot {
  @apply bg-error-500;
}
.event-fc-color.fc-bg-primary .fc-daygrid-event-dot {
  @apply bg-brand-500;
}
.event-fc-color.fc-bg-warning .fc-daygrid-event-dot {
  @apply bg-orange-500;
}
.fc-direction-ltr .fc-timegrid-slot-label-frame {
  @apply px-3 py-1.5 text-left text-sm font-medium text-gray-500 dark:text-gray-400;
}
.fc .fc-timegrid-axis-cushion {
  @apply text-sm font-medium text-gray-500 dark:text-gray-400;
}
.custom-calendar .fc-h-event {
  background-color: transparent;
  border: none;
  color: black;
}
`.trim();
