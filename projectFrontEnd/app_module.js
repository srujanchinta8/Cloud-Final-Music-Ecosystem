CustomerApp = angular.module('CustomerApp', [
    'ngRoute', 'ngFileUpload'
]);

angular.module('CustomerApp').config(['$locationProvider', '$routeProvider',
    function config($locationProvider, $routeProvider) {
        $locationProvider.hashPrefix('!');

        console.log("In route setup.");

        $routeProvider.
        when('/', {
            templateUrl: 'templates/home.template.html'
        }).
        otherwise({
            templateUrl: 'templates/home.template.html'
        })
    }
]);