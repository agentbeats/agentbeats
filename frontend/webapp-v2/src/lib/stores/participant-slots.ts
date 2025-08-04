import { writable } from 'svelte/store';

export type ParticipantSlot = {
  agent: any;
  type: 'opponent';
} | null;

function createParticipantSlotsStore() {
  const { subscribe, set, update } = writable<ParticipantSlot[]>([]);

  return {
    subscribe,
    setSlots: (slots: ParticipantSlot[]) => set(slots),
    setSlot: (index: number, slot: ParticipantSlot) => {
      update(slots => {
        const newSlots = [...slots];
        newSlots[index] = slot;
        return newSlots;
      });
    },
    clearSlots: () => set([]),
    getSlots: () => {
      let slots: ParticipantSlot[] = [];
      subscribe(value => slots = value)();
      return slots;
    }
  };
}

export const participantSlotsStore = createParticipantSlotsStore(); 