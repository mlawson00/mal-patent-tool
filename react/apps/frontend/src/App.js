import React, {Component, useState} from 'react';


class App extends Component {

    state = {
        producerLoginRedirectEndpoint: 'api/login-redirect',
        producerLoginEndpoint: 'http://localhost:8000/api/login/',
        producerLogoutEndpoint: 'api/logout/',
        producerLoginCheckEndpoint: 'api/user-session-status/',
        userLoggedIn: false,
        userName: null,
    }

    componentDidMount() {
        this.authenticate()
    }

    setCookie = (cname, cvalue, exdays) => {
        var d = new Date();
        d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
        var expires = "expires=" + d.toUTCString();
        document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
    }

    getCookie = (cname) => {
        var name = cname + "=";
        var decodedCookie = decodeURIComponent(document.cookie);
        var ca = decodedCookie.split(';');
        for (var i = 0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) === 0) {
                return c.substring(name.length, c.length);
            }
        }
        return "";
    }

    authenticate = () => {
        var authToken = (window.location.search.match(/authToken=([^&]+)/) || [])[1]
        window.history.pushState('object', document.title, "/");

        if (authToken) {
            // Try to get an access token from the server
            this.getAccessToken(authToken)
        } else {
            // Check user is logged in
            this.checkUserSessionStatus()
        }
    }

    getAccessToken = (authToken) => {
        const request = {
            method: 'GET',
            headers: {
                "Authorization": "Bearer " + authToken
            },
            credentials: 'include'
        }

        fetch(this.state.producerLoginEndpoint, request)
            .then(response => {
                // Check user is logged in
                this.checkUserSessionStatus()
            })
            .then(data => {
            })
            .catch(err => {
            })
    }

    checkUserSessionStatus = () => {
        const request = {
            method: 'GET',
            credentials: 'include'
        }

        fetch(this.state.producerLoginCheckEndpoint, request)
            .then(response => response.json())
            .then(data => {
                this.setState({
                    userLoggedIn: data['userLoggedIn'],
                    userName: data['userName'],
                })
            })
            .catch(err => {
            })
    }

    logout = () => {
        const request = {
            method: 'GET',
            credentials: 'include'
        }

        fetch(this.state.producerLogoutEndpoint, request)
            .then(response => response.json())
            .then(data => {
                window.location.reload()
            })
            .catch(err => {
            })
    }

    getPatentData = () => {

        const [searchTerm, setSearchTerm] = useState('')
        const [tokens, setTokens] = useState([])
        const [searchedTerm, setSearchedTerm] = useState('')
        const [processedQuery, setProcessedQuery] = useState('')
        const [loading, setLoading] = useState(false)
        const [probabilityJSX, setProbabilityJSX] = useState(null)
        const [retPatentJSX, setRetPatentJSX] = useState(null)
        const [customEmbedding, setCustomEmbedding] = useState([])
        const [decentAbstract, setDecentAbstract] = useState(false)


        const handleChange = (event) => {
            setSearchTerm(event.target.value)
        };

        const getCustomEmbeddings = (response) => {

            const requestOptions = {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'probs': response.probs
                })}

                fetch('http://localhost:8000/api/give_custom_embedding', requestOptions)
                .then((response) => response.json()).then((response)=>{setCustomEmbedding(JSON.parse(response)['raw_emb'])})
        }

        const getSimilarPatents = () => {

            const requestOptions = {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'embedding': customEmbedding,
                    'k': 10,
                    'use_custom_embeddings': false,
                    'n':3,
                    'query': 'grant_date > 20080101',
                    'with_v1':false
                })}

                fetch('http://localhost:8000/api/give_similar_patents', requestOptions)
                .then((response) => response.json()).then((response)=> {
                    const p_array = JSON.parse(JSON.parse(response)['predictions']);
                    console.log(typeof p_array, p_array)
                    const patent_data = p_array.map((item)=>{
                        const addr = 'https://patents.google.com/patent/'+item.publication_number.split("-").join("")
                        return(<><h2>{item.publication_number}: {item.title}:</h2><div>({Math.round(item.Similarity*100,4)}%)</div>
                            <a href={addr} target = "_blank">{addr}</a>
                        <p>{item.abstract}</p></>)
                    })
                    setRetPatentJSX(patent_data)
                })
        }


        const giveProbs = (response) => {

            console.log('in give probs')
            console.log(response)

            const requestOptions = {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'probs': response.probs
                })
            }
            fetch('http://localhost:8000/api/give_likely_classes', requestOptions)
                .then((response) => {
                    setDecentAbstract(false)
                    setProbabilityJSX('Loading');
                    return (response.json())
                })
                .then((prob_list) => handleProbList(prob_list))
        }

        const makeProbEntry = (prob_row) => {
            const prob_jsx = <p>
                <strong>{prob_row.CPC4}: </strong>{prob_row.title}: - <strong>{prob_row['probability (%)']}%</strong>
            </p>
            return(prob_jsx)
        }

        const handleProbList = (prob_list) => {
            const it = prob_list.map((key, value) => JSON.parse(key))
            if (it[0].length === 0) {
                setDecentAbstract(false)
                setProbabilityJSX('It is unlikely that the query you have provided adequately resembles a patent abstract');
            } else {
                setDecentAbstract(true)
                setProbabilityJSX(it[0].map((item) => makeProbEntry(item)));
            }
            console.log(it)

            // prob_list.map((item)=> console.log(item.id))
            // console.log(prob_list[0])
            // prob_list.map((entry)=> {console.log(entry)})
        }

        const processResponse = (response) => {

            setTokens(response.inputs.text)
            console.log(response.inputs.text)
            setLoading(true)

            const requestOptions = {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'input_mask': response.inputs.input_mask,
                    'input_type_ids': response.inputs.input_type_ids,
                    'input_word_ids': response.inputs.input_word_ids
                })
            }

            fetch('http://localhost:8000/api/get_BERT_probs', requestOptions)
                .then((response) => response.json())
                .then((response) => {giveProbs(response); getCustomEmbeddings(response)})
        }

        const evaluateSearchQuery = () => {

            const requestOptions = {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'abstract': searchTerm})
            }

            fetch('api/abstract_search', requestOptions).then((response) => response.json()).then((response => processResponse(response)))
                .then(() => setSearchedTerm(searchTerm))
        }

        const yikes = tokens.map(name => <strong>{name} </strong>)


        return (
            <div>
                <button onClick={evaluateSearchQuery}>Get Data</button>
                <input id="search" type="text" onChange={handleChange}/>
                {searchedTerm !== "" ?
                    <><p>Searching for: <strong>{searchedTerm}</strong></p>
                        <p>Tokens: {yikes}</p>
                        <p>{probabilityJSX}</p>{decentAbstract && <button onClick={getSimilarPatents}>Get Similar Patents</button>}
                        <p>{retPatentJSX}</p>
                    </>
                    : null}
            </div>
        )
    }

    render() {
        return (
            <section id="page-container">
                {this.state.userLoggedIn ?
                    <div>
                        <div>
                            You are now logged in!
                        </div>
                        <this.getPatentData></this.getPatentData>
                        <div>
                            <button onClick={this.logout}>Logout</button>
                        </div>
                    </div> :
                    //  this is the pair of login boxes, maybe could be fleshed out more!
                    <this.getPatentData></this.getPatentData>
                    // <Login producerLoginRedirectEndpoint={this.state.producerLoginRedirectEndpoint}/>
                }
            </section>
        );
    }
}


function Login(props) {
    const googleLogin = () => {
        var auth_provider = "google-oidc"
        var login_url = props.producerLoginRedirectEndpoint + "?auth_provider=" + auth_provider
        console.log("the login_ur is", login_url)
        window.location.href = login_url
    }

    return (
        <section>
            <div>
                <button onClick={googleLogin}>Login with Google</button>
            </div>
        </section>
    );
}

export default App;