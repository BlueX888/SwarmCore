import { deepMergeOptions } from "./merge-options";

/** TailAdmin Carousel theme — Swiper presets and CSS helpers */

export const carouselPageGridClass =
  "grid grid-cols-1 gap-5 xl:grid-cols-2 xl:gap-6";

export const carouselShellClass =
  "border border-gray-200 rounded-lg dark:border-gray-800";

export const carouselSlideWrapperClass = "overflow-hidden rounded-lg";

export const carouselImageClass = "w-full rounded-lg";

/** Shared autoplay — 5s delay, resume after interaction */
export const defaultCarouselAutoplay = {
  delay: 5000,
  disableOnInteraction: false,
} as const;

/** SlideOnly — carouselOne */
export const slideOnlySwiperOptions = {
  autoplay: defaultCarouselAutoplay,
} as const;

/** WithControl — carouselTwo, prev-style-one / next-style-one */
export const withControlSwiperOptions = {
  autoplay: defaultCarouselAutoplay,
  navigation: {
    nextEl: ".swiper-button-next.next-style-one",
    prevEl: ".swiper-button-prev.prev-style-one",
  },
} as const;

/** WithIndicators — carouselThree */
export const withIndicatorsSwiperOptions = {
  autoplay: defaultCarouselAutoplay,
  pagination: {
    el: ".swiper-pagination",
    clickable: true,
  },
} as const;

/** WithControlAndIndicators — carouselFour */
export const withControlAndIndicatorsSwiperOptions = {
  autoplay: defaultCarouselAutoplay,
  pagination: {
    el: ".swiper-pagination",
    clickable: true,
  },
  navigation: {
    nextEl: ".swiper-button-next.next-style-two",
    prevEl: ".swiper-button-prev.prev-style-two",
  },
} as const;

/** Shallow merge — 仅顶层 key；含 navigation/pagination 的 preset 请用 mergeSwiperOptionsDeep（见 references/merge-options-guide.md） */
export function mergeSwiperOptions<T extends Record<string, unknown>>(
  base: T,
  overrides?: Partial<T> & Record<string, unknown>
): T & Record<string, unknown> {
  return { ...base, ...overrides };
}

/** Deep merge for Swiper preset — 保留 base navigation/pagination 并覆盖子 key */
export function mergeSwiperOptionsDeep<T extends Record<string, unknown>>(
  base: T,
  overrides?: Partial<T> & Record<string, unknown>
): T & Record<string, unknown> {
  return deepMergeOptions(base, overrides);
}

export const carouselNavButtonBaseClass =
  "swiper-button-prev h-10 w-10 rounded-full border-[0.5px] border-white/10 bg-white/90 !text-gray-700 shadow-slider-navigation backdrop-blur-[10px] dark:!text-gray-700";

export const carouselNavPrevClass = `${carouselNavButtonBaseClass} !left-3 sm:!left-4`;

export const carouselNavNextClass =
  "swiper-button-next h-10 w-10 rounded-full border-[0.5px] border-white/10 bg-white/90 !text-gray-700 shadow-slider-navigation backdrop-blur-[10px] !right-3 sm:!right-4 dark:!text-gray-700";

export const stocksSliderNavClass =
  "!static mt-0 h-8 w-9 rounded-full border border-gray-200 !text-gray-700 transition hover:bg-gray-100 dark:border-white/[0.03] dark:bg-gray-800 dark:!text-gray-400 dark:hover:bg-white/[0.05] dark:hover:!text-white/90";

/** Global Swiper CSS overrides for host index.css */
export const swiperCssOverrides = `
.swiper-button-prev svg,
.swiper-button-next svg {
  height: auto !important;
  width: auto !important;
}
.carouselTwo .swiper-button-next:after,
.carouselTwo .swiper-button-prev:after,
.carouselFour .swiper-button-next:after,
.carouselFour .swiper-button-prev:after {
  display: none;
}
.carouselTwo .swiper-button-next.swiper-button-disabled,
.carouselTwo .swiper-button-prev.swiper-button-disabled,
.carouselFour .swiper-button-next.swiper-button-disabled,
.carouselFour .swiper-button-prev.swiper-button-disabled {
  background-color: rgba(255, 255, 255, 0.6) !important;
  opacity: 1 !important;
}
.carouselTwo .swiper-button-next,
.carouselTwo .swiper-button-prev,
.carouselFour .swiper-button-next,
.carouselFour .swiper-button-prev {
  height: 2.5rem;
  width: 2.5rem;
  border-radius: 9999px;
  border-width: 0.5px;
  border-color: rgba(255, 255, 255, 0.1);
  background-color: rgba(255, 255, 255, 0.9);
  color: var(--color-gray-700);
  box-shadow: var(--shadow-slider-navigation);
  backdrop-filter: blur(10px);
}
.carouselTwo .swiper-button-prev,
.carouselFour .swiper-button-prev {
  left: 0.75rem !important;
}
@media (min-width: 640px) {
  .carouselTwo .swiper-button-prev,
  .carouselFour .swiper-button-prev {
    left: 1rem !important;
  }
}
.carouselTwo .swiper-button-next,
.carouselFour .swiper-button-next {
  right: 0.75rem !important;
}
@media (min-width: 640px) {
  .carouselTwo .swiper-button-next,
  .carouselFour .swiper-button-next {
    right: 1rem !important;
  }
}
.carouselThree .swiper-pagination,
.carouselFour .swiper-pagination {
  bottom: 0.75rem !important;
  left: 50% !important;
  display: inline-flex !important;
  width: auto !important;
  transform: translateX(-50%);
  align-items: center;
  gap: 0.375rem;
  border-radius: 40px;
  border-width: 0.5px;
  border-color: rgba(255, 255, 255, 0.1);
  background-color: rgba(255, 255, 255, 0.6);
  padding: 0.375rem 0.5rem;
  box-shadow: var(--shadow-slider-navigation);
  backdrop-filter: blur(10px);
}
@media (min-width: 640px) {
  .carouselThree .swiper-pagination,
  .carouselFour .swiper-pagination {
    bottom: 1.25rem !important;
  }
}
.carouselThree .swiper-pagination-bullet,
.carouselFour .swiper-pagination-bullet {
  margin: 0 !important;
  height: 0.625rem;
  width: 0.625rem;
  background-color: white;
  opacity: 1;
  box-shadow: var(--shadow-theme-xs);
  transition-duration: 200ms;
  transition-timing-function: ease-in-out;
}
.carouselThree .swiper-pagination-bullet-active,
.carouselFour .swiper-pagination-bullet-active {
  width: 1.625rem;
  border-radius: 0.75rem;
}
.stocks-slider-outer .swiper-button-next:after,
.stocks-slider-outer .swiper-button-prev:after {
  display: none;
}
.stocks-slider-outer .swiper-button-next,
.stocks-slider-outer .swiper-button-prev {
  position: static !important;
  margin-top: 0;
  height: 2rem;
  width: 2.25rem;
  border-radius: 9999px;
  border: 1px solid var(--color-gray-200);
  color: var(--color-gray-700);
  transition: background-color 150ms;
}
.stocks-slider-outer .swiper-button-next.swiper-button-disabled,
.stocks-slider-outer .swiper-button-prev.swiper-button-disabled {
  background-color: white;
  opacity: 0.5;
}
.dark .stocks-slider-outer .swiper-button-next.swiper-button-disabled,
.dark .stocks-slider-outer .swiper-button-prev.swiper-button-disabled {
  background-color: var(--color-gray-900);
}
.dark .stocks-slider-outer .swiper-button-next,
.dark .stocks-slider-outer .swiper-button-prev {
  border-color: rgba(255, 255, 255, 0.03);
  background-color: var(--color-gray-800);
  color: var(--color-gray-400);
}
` as const;
