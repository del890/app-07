/**
 * Sorte UI — public entry point.
 *
 * In a Nuxt app, import the stylesheet once (e.g. in nuxt.config `css: []`)
 * and import components where needed, or register them globally via a plugin.
 *
 *   import 'sorte-ui/styles';
 *   import { SButton, SCard } from 'sorte-ui';
 */
import SIcon from './components/Icon/SIcon.vue';
import SHeading from './components/Typography/SHeading.vue';
import SText from './components/Typography/SText.vue';
import SButton from './components/Button/SButton.vue';
import SBadge from './components/Badge/SBadge.vue';
import SAvatar from './components/Avatar/SAvatar.vue';
import SDivider from './components/Divider/SDivider.vue';
import SCard from './components/Card/SCard.vue';
import STabs from './components/Tabs/STabs.vue';
import SInput from './components/Input/SInput.vue';
import SAppHeader from './components/Header/SAppHeader.vue';
import SLotteryBall from './components/Lottery/SLotteryBall.vue';
import SThemePicker from './components/Lottery/SThemePicker.vue';

export {
  SIcon,
  SHeading,
  SText,
  SButton,
  SBadge,
  SAvatar,
  SDivider,
  SCard,
  STabs,
  SInput,
  SAppHeader,
  SLotteryBall,
  SThemePicker,
};

export const components = {
  SIcon, SHeading, SText, SButton, SBadge, SAvatar, SDivider,
  SCard, STabs, SInput, SAppHeader, SLotteryBall, SThemePicker,
};

/** Vue plugin: `app.use(SorteUI)` registers every component globally. */
export const SorteUI = {
  install(app) {
    for (const [name, comp] of Object.entries(components)) {
      app.component(name, comp);
    }
  },
};

export { lotteries, themes, color, font, space, radius, shadow } from './tokens.js';

export default SorteUI;
