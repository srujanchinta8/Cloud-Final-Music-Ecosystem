CustomerApp.controller("myCtrl", function($scope, $http, $routeParams, $location, $window, Upload) {

    console.log($location.absUrl());

    //Cognito Login
    /*
    let id_token_array = new URL($location.absUrl()).hash.split('&').filter(function(el) { if(el.match('id_token') !== null) return true; });
    let user_email = null;

    let notLoggedInRedirectURL = "https://cloud-project-kr2789.auth.us-east-1.amazoncognito.com/login?response_type=token&client_id=701t6b2qghk9e5a1fp93foslfl&redirect_uri=https://dp8soa4lnhdrx.cloudfront.net";

    if (id_token_array != null && id_token_array.length != 0) {
        id_token = id_token_array[0].split('=')[1];
        console.log(id_token);

        let decoded = jwt_decode(id_token);
        user_email = decoded['email'];
        console.log(decoded);
        console.log(user_email);
    } else {
        $window.location.href = notLoggedInRedirectURL;
    }
    */


    let access_token_array = $location.url().match(/\#(?:access_token)\=([\S\s]*?)\&/);
    let spotify_access_token = null;

    // Below is Spotify Login
    if (access_token_array == null) {
        // Get the hash of the url
        const hash = window.location.hash
            .substring(1)
            .split('&')
            .reduce(function (initial, item) {
                if (item) {
                    var parts = item.split('=');
                    initial[parts[0]] = decodeURIComponent(parts[1]);
                }
                return initial;
            }, {});
        window.location.hash = '';

        // Set token
        let _token = hash.access_token;

        const authEndpoint = 'https://accounts.spotify.com/authorize';

        // Replace with your app's client ID, redirect URI and desired scopes
        const clientId = 'XXX';
        //const redirectUri = 'http://localhost:3000/project';
        const redirectUri = 'https://dp8soa4lnhdrx.cloudfront.net';
        const scopes = [
            'user-read-birthdate',
            'user-read-email',
            'user-read-private',
            'playlist-modify-private',
            'playlist-modify-public'
        ];

        // If there is no token, redirect to Spotify authorization
        if (!_token) {
            window.location = `${authEndpoint}?client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scopes.join('%20')}&response_type=token`;
        }
    } else {
        spotify_access_token = access_token_array[1];
        console.log(spotify_access_token);
    }


    $scope.chatURL = "https://g99exy2urf.execute-api.us-east-1.amazonaws.com/testing/chatbot";

    $scope.s3AudioBucketURL = "https://s3.amazonaws.com/cloud-project-audiobucket/";

    $scope.s3ImageBucketCreds = {
        bucket: 'cloud-project-imagebucket',
        access_key: 'XXX',
        secret_key: 'XXX'
    };

    $scope.imageSearchURL = "https://g99exy2urf.execute-api.us-east-1.amazonaws.com/testing/searchbyimage";

    //Audio Input
    $scope.rec = new webkitSpeechRecognition();
    $scope.interim = '';
    $scope.final = '';

    let self = $scope;

    $scope.rec.continuous = false;
    $scope.rec.lang = 'en-US';
    $scope.rec.interimResults = true;
    $scope.rec.onerror = function(event) {
        console.log('error!');
    };

    $scope.start = function() {
        console.log('Should start recording');
        self.rec.start();
    };

    $scope.rec.onresult = function(event) {
        for(var i = event.resultIndex; i < event.results.length; i++) {
            if(event.results[i].isFinal) {
                $scope.final = $scope.final.concat(event.results[i][0].transcript);
                // clearing interim
                $scope.interim = '';
                //$scope.$apply();
                //$scope.searchTextBox = event.results[i][0].transcript;
                let transcribeResult = event.results[i][0].transcript;
                document.getElementById('searchTextBoxId').value = transcribeResult;
                console.log(transcribeResult);
                sendFunction();
            } else {
                $scope.interim = '';
                //$scope.$apply();
                $scope.interim = $scope.interim.concat(event.results[i][0].transcript);
                //$scope.$apply();
            }
        }
    };

    //Chat interaction
    $scope.searchButtonClick = function() {
        sendFunction();
    };

    function sendFunction() {
        let text = document.getElementById('searchTextBoxId').value;
        addSenderTextToUI(text);
        document.getElementById('searchTextBoxId').value = '';

        makeSendCalloutAndReceive(text);
    }

    function makeSendCalloutAndReceive(inputText) {
        $scope.image_url_list = [];

        let url = $scope.chatURL;

        req = {
            "message":
                {
                    "type": "string",
                    "content": {
                        "text": inputText,
                        "spotify_token": spotify_access_token
                    }
                }
        };

        $http.post(url, req, headers = {"Access-Control-Allow-Origin": "*"}).then(
            function(result) {
                console.log("Result = " + JSON.stringify(result));
                response_body = result['data']['result'];

                let textMessage = response_body['text'];

                let audioURL = $scope.s3AudioBucketURL + response_body['s3_uuid'] + '.mp3';
                console.log("Audio URL = " +  audioURL);
                let audio = new Audio(audioURL);
                audio.play();

                addReceiverTextToUI(textMessage);
                //clickBtn("_from", parseReponseString(result['data']['message']));

                if('track_url' in response_body) {
                    addReceiverSongToUI(response_body['track_url']);
                }

            },
            function(error) {
                console.log("Result = " + JSON.stringify(error));
                //clickBtn("_from", 'Something went wrong. Contact administrator.');
            }
        );
    };

    function addSenderTextToUI(text) {
        var $chatlogs = $('.chatlogs');

        $chatlogs.append(
            $('<div/>', {'class': 'chat self'}).append(
                $('<p/>', {'class': 'chat-message', 'text': text})));
    };

    function addReceiverTextToUI(text) {
        var $chatlogs = $('.chatlogs');

        $chatlogs.append(
            $('<div/>', {'class': 'chat friend'}).append(
                '<div class="user-photo"><img src="images/ana.JPG"></div>',
                $('<p/>', {'class': 'chat-message', 'text': text})));
    };

    function addReceiverSongToUI(songURL) {
        var $chatlogs = $('.chatlogs');

        /*
        $chatlogs.append(
            $('<div/>', {'class': 'chat friend'}).append(
                '<div class="user-photo"><img src="images/ana.JPG"></div>',
                $('<p/>', {'class': 'chat-message', 'text': text})));
        */
        $chatlogs.append(
            $('<div/>', {'class': 'chat friend'}).append(
                '<audio controls><source type="audio/mpeg" src="' + songURL + '">Your browser does not support the audio element.<audio/>'));
    };

    //Upload Photo
    $scope.uploadPhoto = function(photo){
        //amazon aws credentials
        AWS.config.update({
            accessKeyId : $scope.s3ImageBucketCreds.access_key,
            secretAccessKey : $scope.s3ImageBucketCreds.secret_key
        });
        //amazon s3 region
        AWS.config.region = 'us-east-1';
        let image_name = uuidv4();
        //amazon s3 bucket name
        var bucket = new AWS.S3({params: {Bucket: $scope.s3ImageBucketCreds.bucket}});
        var params = {Key: image_name, ContentType: photo.type, Body: photo};
        bucket.upload(params).on('httpUploadProgress', function(evt) {
            //logs the image uploading progress
            console.log("Uploaded :: " + parseInt((evt.loaded * 100) / evt.total)+'%');
            var progress=parseInt((evt.loaded * 100) / evt.total);
            if(progress === 100){
                alert("Photo Uploaded Successfully");
            }
        }).send(function(err, data) {
            if (data) {
                //displays the image location on amazon s3 bucket
                console.log(data.Location);
                sendFileForImageRecognition(image_name);
                addSenderImageToUI(data.Location);
            }
        });
    };

    function addSenderImageToUI(image_url) {
        var $chatlogs = $('.chatlogs');

        $chatlogs.append(
            $('<div/>', {'class': 'chat self'}).append(
                '<div class="gif"><img src="' + image_url + '"></div>'));
    };

    function uuidv4() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    //Send uploaded file URL to lambda function for image recognition
    function sendFileForImageRecognition(image_name) {

        let url = $scope.imageSearchURL;

        req = {
            "image_name": image_name,
            "spotify_token": spotify_access_token
        };

        $http.post(url, req, headers = {"Access-Control-Allow-Origin": "*"}).then(
            function(result) {
                console.log("Result = " + JSON.stringify(result));
                response_body = result['data']['result'];
                addReceiverTextToUI(response_body);
            },
            function(error) {
                console.log("Result = " + JSON.stringify(error));
            }
        );
    };


});

