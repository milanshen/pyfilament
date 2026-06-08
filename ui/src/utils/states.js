const INCOMPLETE_STATES = ['created', 'running', 'timeout', 'retrying'];
const SUCCESS_STATES = ['success', 'cached'];
const FAILURE_STATES = ['failure', 'cancelled'];
const COMPLETE_STATES = [...SUCCESS_STATES, ...FAILURE_STATES];
const ALL_STATES = [...INCOMPLETE_STATES, ...COMPLETE_STATES];

const STATE_FILTERS = {
    all: ALL_STATES,
    incomplete: INCOMPLETE_STATES,
    success: SUCCESS_STATES,
    failure: FAILURE_STATES,
};

function getStates(statesFilter = 'all') {
    return STATE_FILTERS[statesFilter] ?? ALL_STATES;
}

export { getStates };
