import _ from 'lodash';

export function sortKeys(obj) {
    if (Array.isArray(obj)) {
        return obj.map(sortKeys);
    } else if (obj && typeof obj === 'object') {
        return Object.keys(obj)
            .sort()
            .reduce((acc, key) => {
                acc[key] = sortKeys(obj[key]);
                return acc;
            }, {});
    }
    return obj;
}

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
