var _queryBeingDone = null;
var _pattern = null;
var _escapedRegex = /[-\/\\^$*+?.()|[\]{}]/g;
function escapeRegex(e) {
    return e.replace(_escapedRegex, '\\$&');
}

// for some reason Sphinx shows some entries twice
// if something has been scored already I'd rather sort it to the bottom
var _beenScored = new Set();

function __score(haystack, regex) {
    let match = regex.exec(haystack);
    if(match == null) {
        return Number.MAX_VALUE;
    }
    let subLength = match[0].length;
    let start = match.index;
    return (subLength * 1000 + start) / 1000.0;
}

// unused for now
function __cleanNamespaces(query) {
    return query.replace(/(discord\.(ext\.)?)?(.+)/, '$3');
}

var Scorer = {
    // Implement the following function to further tweak the score for each result
    // The function takes a result array [filename, title, anchor, descr, score]
    // and returns the new score.

    score: function(result) {
      // only inflate the score of things that are actual API reference things
      if(_pattern !== null && result[1].startsWith('discord.')) {
        let _score = __score(result[1], _pattern);
        if(_score === Number.MAX_VALUE) {
            return result[4];
        }
        if(_beenScored.has(result[1])) {
            return 0;
        }
        _beenScored.add(result[1]);
        let newScore = 100 + _queryBeingDone.length - _score;
        // console.log(`${result[1]}: ${result[4]} -> ${newScore} (${_score})`);
        return newScore;
      }
      return result[4];
    },


    // query matches the full name of an object
    objNameMatch: 15,
    // or matches in the last dotted part of the object name
    objPartialMatch: 11,
    // Additive scores depending on the priority of the object
    objPrio: {0:  15,   // used to be importantResults
              1:  7,   // used to be objectResults
              2: -5},  // used to be unimportantResults
    //  Used when the priority is not in the mapping.
    objPrioDefault: 0,

    // query found in title
    title: 15,
    partialTitle: 7,
    // query found in terms
    term: 5,
    partialTerm: 2
};


$(document).ready(function() {
    let params = $.getQueryParameters();
    if(params.q) {
        _queryBeingDone = params.q[0];
        let pattern = Array.from(_queryBeingDone).map(escapeRegex).join('.*?');
        _pattern = new RegExp(pattern, 'i');
    }
});
