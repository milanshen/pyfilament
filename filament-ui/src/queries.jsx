import { gql } from '@apollo/client';

const GET_TASK_RUN_BREADCRUMB = gql`
    query GetTaskRunBreadcrumb($uuid: String!) {
        getTaskRun(taskUuid: $uuid) {
            id
            taskUuid
            name
            state
            stateSince
            parentTaskUuid
            taskType {
                id
                name
                funcAddress
            }
        }
    }
`;

const GET_TASK_RUN = gql`
    query GetTaskRun($id: ID!) {
        getTaskRun(id: $id) {
            id
            taskUuid
            name
            createdAt
            state
            stateSince
            heartbeat
            runCount
            parentTaskUuid
            taskType {
                id
                name
                funcAddress
            }
            stateTransitions {
                id
                taskUuid
                fromState
                toState
                stateSince
            }
            logs {
                timestamp
                name
                level
                message
            }
            childTasks {
                id
            }
            parametersJson
            resultJson
        }
    }
`;

const GET_TASK_RUN_LOGS = gql`
    query GetTaskRunLogs($id: ID!) {
        getTaskRun(id: $id) {
            id
            logs {
                timestamp
                name
                level
                message
            }
        }
    }
`;

const GET_TASK_TYPE = gql`
    query GetTaskType($id: ID!) {
        getTaskType(id: $id) {
            id
            name
            funcAddress
            taskRuns {
                id
                taskUuid
                name
                createdAt
                state
                stateSince
                heartbeat
                runCount
                parentTaskUuid
                parametersJson
            }
        }
    }
`;

const GET_TASK_RUNS = gql`
    query GetTaskRuns($taskTypeId: ID!, $states: [String!]!) {
        getTaskRuns(taskTypeId: $taskTypeId, states: $states) {
            id
            taskUuid
            name
            createdAt
            state
            stateSince
            heartbeat
            runCount
            parentTaskUuid
            parametersJson
        }
    }
`;

const GET_TASK_TYPES = gql`
    query GetTaskTypes {
        getTaskTypes {
            id
            name
            funcAddress
            latestTaskRun {
                id
                taskUuid
                name
                createdAt
                state
                stateSince
            }
        }
    }
`;

const CANCEL_TASK_RUN = gql`
    mutation CancelTaskRun($id: ID!) {
        cancelTaskRun(id: $id) {
            id
            state
        }
    }
`;

export {
    CANCEL_TASK_RUN,
    GET_TASK_RUN,
    GET_TASK_RUN_BREADCRUMB,
    GET_TASK_RUN_LOGS,
    GET_TASK_RUNS,
    GET_TASK_TYPE,
    GET_TASK_TYPES,
};
