import React, {Component, useState} from 'react';
import Login_page from "./login_page";

class App extends Component {

    state = {
        producerLoginRedirectEndpoint: 'api/login-redirect',
        producerLoginEndpoint: 'api/login/',
        producerLogoutEndpoint: 'api/logout/',
        producerLoginCheckEndpoint: 'api/user-session-status/',
        userLoggedIn: false,
        userName: null,
        country_ob: {
            "AP": {selected: false, name: "African Regional Industrial Property Organization"},
            "DZ": {selected: false, name: "Algeria"},
            "AR": {selected: false, name: "Argentina"},
            "AU": {selected: false, name: "Australia"},
            "AT": {selected: false, name: "Austria"},
            "BE": {selected: false, name: "Belgium"},
            "BA": {selected: false, name: "Bosnia and Herzegovina"},
            "CA": {selected: false, name: "Canada"},
            "CL": {selected: false, name: "Chile"},
            "CN": {selected: false, name: "China"},
            "DK": {selected: false, name: "Denmark"},
            "EG": {selected: false, name: "Egypt"},
            "EP": {selected: false, name: "European Patent Organization"},
            "FI": {selected: false, name: "Finland"},
            "FR": {selected: false, name: "France"},
            "DE": {selected: false, name: "Germany"},
            "IT": {selected: false, name: "Italy"},
            "JP": {selected: false, name: "Japan"},
            "JO": {selected: false, name: "Jordon"},
            "KR": {selected: false, name: "Korea"},
            "LU": {selected: false, name: "Luxembourg"},
            "GC": {selected: false, name: "Patent Office of the Cooperation Council for the Arab States of the Gulf"},
            "NL": {selected: false, name: "Netherlands"},
            "RU": {selected: false, name: "Russian Federation"},
            "ES": {selected: false, name: "Spain"},
            "TW": {selected: false, name: "Taiwan"},
            "GB": {selected: true, name: "United Kingdom"},
            "US": {selected: false, name: "United States"},
            "SU": {selected: false, name: "USSR"}
        },
        start_year: 1900,
        end_year: 2022,
        status: "Inactive"
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

    GetPatentData = () => {

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
                })
            }

            fetch('api/give_custom_embedding', requestOptions)
                .then((response) => response.json()).then((response) => {
                setCustomEmbedding(JSON.parse(response)['raw_emb'])
            })
        }


        const getSimilarPatents = () => {

            const requestOptions = {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'embedding': customEmbedding,
                    'k': 10,
                    'query': {
                        'start_year': this.state.start_year,
                        'end_year': this.state.end_year,
                        'countries': this.state.country_ob
                    }
                })
            }

            fetch('api/give_similar_patents_bq', requestOptions).then((response) => {
                this.setState({'status': 'Retrieving similar patents'}, console.log('updated status'))
                if (!response.ok) {
                    console.log(response)
                    const bad_news = <div>Unfortunately, this did not work. Perhaps altering your query parameters would
                        help?</div>
                    setRetPatentJSX(bad_news)
                    this.setState({'status': 'Inactive'})
                    // throw Error(response.statusText);
                }
                return response;
            })
                .then((response) => response.json()).then((response) => {
                console.log(response)
                const p_array = JSON.parse(response['predictions']);
                const cost = response['cost']
                console.log('that cost', cost)
                const patent_data = p_array.map((item) => {
                    const addr = 'https://patents.google.com/patent/' + item.publication_number.split("-").join("")
                    console.log(item);
                    var filing_date = new Date(item.filing_date)
                    var grant_date = new Date(item.grant_date)

                    return (

                        <><h2>{item.publication_number}</h2>
                            <h2>Title: {item.title}</h2>
                            <div>Estimated Match: {Math.round((1 - item.cosine_distance) * 100, 4)}%)</div>
                            <div>link: <a href={addr} target="_blank">{addr}</a></div>
                            <div>filing date: {filing_date.toDateString()}</div>
                            <div>grant date: {grant_date.toDateString()}</div>
                            <div>country: {this.state['country_ob'][item.country_code]['name']}</div>
                            <div>kind: {item.kind_code}</div>
                            <h3>Abstract</h3>
                            <div>{((item.abstract.length < 1) ? 'No abstract available' : item.abstract)}</div>
                        </>
                    )
                })
                setRetPatentJSX(<>{patent_data}</>)
            }).then(this.setState({'status': 'Inactive'}), console.log('updated status'))
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
            this.setState({'status': 'looking up likely CPC4 class names'})
            fetch('api/give_likely_classes', requestOptions)
                .then((response) => {
                    console.log("I got a response from give likely classes")
                    setDecentAbstract(false)
                    setProbabilityJSX('Loading');
                    return (response.json())
                })
                .then((prob_list) => handleProbList(prob_list)).then(this.setState({'status': 'Inactive'}))
        }

        const makeProbEntry = (prob_row) => {
            console.log(prob_row)
            const prob_jsx = <p>
                <strong>{prob_row.CPC4}: </strong>
                {prob_row.title}: - <strong>{prob_row['probability (%)']}%</strong>
            </p>
            // return (prob_jsx)
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

            prob_list.map((item) => console.log(item.id))
            console.log(prob_list[0])
            prob_list.map((entry) => {
                console.log(entry)
            })
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
            this.setState({'status': 'retrieving patent CPC4 probabilities'})
            fetch('api/get_BERT_probs', requestOptions)
                .then((response) => response.json())
                .then((response) => {
                    giveProbs(response);
                    getCustomEmbeddings(response)
                }).then(this.setState({'status': 'Inactive'}))
        }

        const evaluateSearchQuery = () => {

            const requestOptions = {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'abstract': searchTerm})
            }
            console.log(searchTerm)
            this.setState({'status': 'tokenizing abstract'})
            fetch('api/abstract_search', requestOptions).then((response) => response.json()).then((response => processResponse(response)))
                .then(() => setSearchedTerm(searchTerm)).then(this.setState({'status': 'Inactive'}))
        }

        const yikes = tokens.map(name => <strong>{name} </strong>)

        console.log('probabilityJSX is ', probabilityJSX)


        return (

            <div>
                <h1>Welcome {this.state.userName}</h1>
                <p>Patent Tool Status: <strong>{this.state.status}</strong></p>
                <button onClick={evaluateSearchQuery}>Get Data</button>
                <input id="search" type="text" onChange={handleChange}/>
                {searchedTerm !== "" ? <>
                    <p>Searching for: <strong>{searchedTerm}</strong></p>
                    <p>Tokens: {yikes}</p>
                    {decentAbstract && <>
                        <p>probabilityJSX</p>
                        <p><button onClick={getSimilarPatents}>Get Similar Patents</button></p>
                        <p>{this.yearDropDown('start_year')}</p>
                        <p>{this.yearDropDown('end_year')}</p>
                        <p>{this.nDropDown('n',1,5)}</p>
                        {this.makeCheckboxes()}
                        <p>{retPatentJSX}</p>
                    </>}


                </> : null}
            </div>

        )


    }


    Selectors = (props) => {

        const jsx = <select>
            <option value="AP">African Regional Industrial Property Organization</option>
            <option value="DZ">Algeria</option>
            <option value="AR">Argentina</option>
            <option value="AU">Australia</option>
            <option value="AT">Austria</option>
            <option value="BE">Belgium</option>
            <option value="BA">Bosnia and Herzegovina</option>
            <option value="CA">Canada</option>
            <option value="CL">Chile</option>
            <option value="CN">China</option>
            <option value="DK">Denmark</option>
            <option value="EG">Egypt</option>
            <option value="EP">European Patent Organization</option>
            <option value="FI">Finland</option>
            <option value="FR">France</option>
            <option value="DE">Germany</option>
            <option value="IT">Italy</option>
            <option value="JP">Japan</option>
            <option value="JO">Jordon</option>
            <option value="KR">Korea</option>
            <option value="LU">Luxembourg</option>
            <option value="GC">Patent Office of the Cooperation Council for the Arab States of the Gulf</option>
            <option value="NL">Netherlands</option>
            <option value="RU">Russian Federation</option>
            <option value="ES">Spain</option>
            <option value="TW">Taiwan</option>
            <option value="GB">United Kingdom</option>
            <option value="US">United States</option>
            <option value="SU">USSR</option>
            <option value="">All (computationally expensive)</option>
        </select>


        return (jsx)
    }


    checkboxClicker = (event) => {
        console.log(event)
        let buttons_state = this.state.country_ob
        if (buttons_state[event.target.id]['selected'] === false) {
            buttons_state[event.target.id]['selected'] = true
        } else {
            buttons_state[event.target.id]['selected'] = false
        }

        this.setState({'country_ob': buttons_state}, console.log('set_button_state'))
    }

    handleCheck = (event) => {
        console.log(event.target)
    };

    makeCheckboxes = (props) => {
        const jsx = Object.entries(this.state.country_ob).map(([key, value]) =>

            <div><input onChange={this.checkboxClicker} type="checkbox" id={key} name={value['name']}
                        checked={value['selected']}/>: {value['name']}</div>
        )
        const output = <div className="country selector">{jsx}</div>
        return (output)
    }


    nDropDown = (id, min, max) => {


        const onHandleChange = (evt) => {
            this.setState({[evt.target['name']]: evt.target.value}, console.log('set the state'));
        };

        const thisYear = (new Date()).getFullYear();

        const selectedYear = this.state[id]

        let minOffset = min
        let maxOffset = max
        const options = [];

        for (let i = minOffset; i <= maxOffset; i++) {
            const n = i;
            options.push(<option value={n}>{n}</option>);
        }

        console.log('the probs id is', this.state[id])

        const jsx = <div>{id}:
            <select value={this.state[id]} onChange={onHandleChange} name={id}>
                {options}
            </select>
        </div>;

        return jsx
    }

    yearDropDown = (id) => {


        const onHandleChange = (evt) => {
            // Handle Change Here
            // alert(evt.target.value);
            // const p = evt.target['name']
            this.setState({[evt.target['name']]: evt.target.value}, console.log('set the state'));
        };

        const thisYear = (new Date()).getFullYear();

        // this.setState({'end_year': thisYear})

        const selectedYear = this.state[id]

        let min_i = 0
        let max_i = 122
        const options = [];
        console.log('the year dropdown props is', id)
        if (id === 'start_year') {
            console.log('!!!!! is was start_year')
            min_i = 1900
            max_i = this.state['end_year']
        } else {
            min_i = this.state['start_year']
            max_i = thisYear
        }


        for (let i = min_i; i <= max_i; i++) {
            options.push(<option value={i}>{i}</option>);
        }

        console.log('the probs id is', this.state[id])

        const jsx = <div>{id}:
            <select value={this.state[id]} onChange={onHandleChange} name={id}>
                {options}
            </select>
        </div>;

        return jsx
    }

    googleLogin = () => {
        var auth_provider = "google-oidc"
        var login_url = this.state.producerLoginRedirectEndpoint + "?auth_provider=" + auth_provider
        console.log("the login_ur is", login_url)
        window.location.href = login_url
    }


    render() {
        return (
            <section id="page-container">
                {this.state.userLoggedIn ?
                    <div>
                        <div>
                            You are now logged in!
                        </div>
                        <this.GetPatentData/>
                        <div>
                            <button onClick={this.logout}>Logout</button>
                        </div>
                    </div> :
                    //  this is the pair of login boxes, maybe could be fleshed out more!
                    <div>
                        {/*<this.GetPatentData/>*/}
                        {/*<this.Selectors></this.Selectors>*/}
                        {/*<input type="checkbox" id='yo' name='uouio' checked={true}/>*/}
                        <Login_page googleLogin = {this.googleLogin}/>


                    </div>

                    // <Login producerLoginRedirectEndpoint={this.state.producerLoginRedirectEndpoint}/>
                }
            </section>
        );
    }

}


export default App;