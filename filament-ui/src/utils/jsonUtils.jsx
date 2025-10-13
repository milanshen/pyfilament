import _ from 'lodash';

export function deepJsonParse(message) {
    if (_.isString(message)) {
        try {
            const parsedMessage = JSON.parse(message);
            return deepJsonParse(parsedMessage);
        } catch (e) {
            return message;
        }
    } else if (_.isPlainObject(message)) {
        return _.mapValues(message, deepJsonParse);
    } else if (_.isArray(message)) {
        return _.map(message, deepJsonParse);
    } else {
        return message;
    }
}
