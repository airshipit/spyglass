// Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


// This file includes all the frond-end functionality being used for the
// yaml editor application.


/**
 * Calls /save URL to save edit progress.
 * @param  {String} data Stringified JSON data.
 */
function save(data) {
    $.ajax({
        type: 'POST',
        url: '/save',
        data: data,
        success: function(res) {
            setTimeout(function() { alert(res); }, 3);
        },
        contentType: 'application/json;charset=UTF-8'
    });
}

/**
 * Calls /saveExit URL to save edit progress and shut down web server.
 * @param  {String} data Stringified JSON data.
 */
function saveAndExit(data) {
    $.ajax({
        type: 'POST',
        url: '/saveExit',
        data: data,
        success: function(res) {
            setTimeout(function() { alert(res); }, 3);
        },
        contentType: 'application/json;charset=UTF-8'
    });
}

/**
 * Collects and validates data from textarea.
 * @returns  {String}  Stringified JSON data.
 */
function getSimpleData() {
    var data = $("#yaml_data").val();
    try {
        var index = data.indexOf(changeStr)
        if (index != -1) {
            var lineNum = data.substring(0, index).split('\n').length;
            alert('Please change value on line '+ lineNum + '!')
            return null
        }
        data = jsyaml.load(data)
    }
    catch(err) {
        alert(err)
        return null
    }
    return JSON.stringify({yaml_data : data})
}

/**
 * Function to save edit progress.
 */
function saveSimple() {
    var data = getSimpleData()
    if (data) {
        save(data)
    }
}

/**
 * Function to save edit progress and shut down web server.
 */
function saveExitSimple() {
    var data = getSimpleData()
    if (data) {
        saveAndExit(data)
    }
}
